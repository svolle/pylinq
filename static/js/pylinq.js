/* global alert, require */
require(['jquery', 'lib/knockout-3.1.0'], function($, ko) {
    'use strict';

    var MIN_PLAYER_COUNT = 2,
        MAX_PLAYER_COUNT = 2,
        IS_SPY = 0,
        IS_COUNTER_SPY = 1;

    var Events = {
        NEW_PLAYER: 'new_player',
        PLAYER_QUIT: 'player_quit',
        NEW_MASTER: 'new_master',
        PLAYER_ROLE_ASSIGNED: 'player_role_assigned',
        GAME_STARTED: 'game_started',
        GAME_ABORTED: 'game_aborted',
        LOST_CONNECTION: 'lost_connection'
    };

    // Using jQuery 1.9.1
    $('body').css('visibility', 'visible');
    $(document).ajaxError(function(event, jqxhr) {
        var response = JSON.parse(jqxhr.responseText);
        if(response.error) {
            alert(response.error);
        }
    });

    var game, playerList, wsController;

    function WebSocketController() {}
    WebSocketController.prototype = {
        connect: function() {
            this.ws = new WebSocket('ws://localhost:8888/socket');

            this.ws.onopen      = this.onOpen.bind(this);
            this.ws.onmessage   = this.onMessage.bind(this);
            this.ws.onclose     = this.onClose.bind(this);
            this.ws.onerror     = this.onError.bind(this);
        },

        send: function(message) {
            this.ws.send(JSON.stringify(message));
        },

        onOpen: function() {
            $(this).trigger('open');
        },

        onMessage: function(message) {
            var data  = JSON.parse(message.data),
                event = data.event;

            $(this).trigger(event, [data]);
        },
        onClose: function() {
            alert('Connection with server closed');
            document.reload();
        },
        onError: function() {
            alert('Error in server connection');
            document.reload();
        }
    };

    ko.bindingHandlers.fadeVisible = {
        init: function(element, valueAccessor) {
            // Start visible/invisible according to initial value
            var shouldDisplay = valueAccessor();
            $(element).toggle(shouldDisplay);
        },
        update: function(element, valueAccessor) {
            // On update, fade in/out
            var shouldDisplay = valueAccessor();
            return shouldDisplay ? $(element).fadeIn() : $(element).fadeOut();
        }
    };

    function Player(data) {
        this.name = ko.observable(data.name);
        this.score = ko.observable(data.score);
    }

    function PlayerListViewModel(webSocketController) {
        var self        = this,
            $ws         = $(webSocketController);
        self.players    = ko.observableArray([]);
        self.hasPlayers = ko.computed(this._hasPlayers, this);

        $ws.bind(Events.NEW_PLAYER,   this.onNewPlayer.bind(this));
        $ws.bind(Events.PLAYER_QUIT,  this.onPlayerQuit.bind(this));
        $ws.bind(Events.GAME_ABORTED, this.onGameAborted.bind(this));

        self.loadPlayers();
    }
    PlayerListViewModel.prototype = {
        _hasPlayers: function() {
            return this.players().length > 0;
        },

        sortPlayers: function(a, b) {
            return a.score() === b.score() ? (a.name() < b.name() ? -1 : 1) : (a.score() < b.score() ? -1 : 1);
        },

        count: function() {
            return this.players().length;
        },

        loadPlayers: function() {
            var self = this;

            $.getJSON('/players', function(allData) {
                $.each(allData, function(idx, playerData) {
                    self.addPlayer(playerData);
                });
            });
        },

        addPlayer: function(playerData) {
            this.players.push(new Player(playerData));
        },

        removePlayer: function(playerName) {
            this.players.remove(function(player) { return player.name() === playerName; });
        },

        onNewPlayer: function(event, data) {
            this.addPlayer(data.player);
        },

        onPlayerQuit: function(event, data) {
            this.removePlayer(data.player_name);
        },

        onGameAborted: function() {
            this.players([]);
        }
    };


    function PyLinq(playerList, webSocketController) {
        this.playerName         = ko.observable('');
        this.playerRole         = ko.observable(false);
        this.getPlayerRole      = ko.computed(this._getPlayerRole, this);
        this.playerList         = playerList;

        this.isConnected        = ko.observable(false);
        this.hasJoined          = ko.observable(false);
        this.isMaster           = ko.observable(false);
        this.isGameStarted      = ko.observable(false);
        this.canStartGame       = ko.computed(this._canStartGame, this);

        this.wsController = webSocketController;

        $(webSocketController)
            .bind('open', this.onConnect.bind(this))
            .bind(Events.NEW_MASTER, this.onNewMaster.bind(this))
            .bind(Events.GAME_STARTED, this.onGameStarted.bind(this))
            .bind(Events.GAME_ABORTED, this.onGameAborted.bind(this))
            .bind(Events.LOST_CONNECTION, this.onLostConnection.bind(this))
            .bind(Events.PLAYER_ROLE_ASSIGNED, this.onRoleAssigned.bind(this));
    }
    PyLinq.prototype = {
        _canStartGame: function() {
            return this.isMaster() &&
                   !this.isGameStarted() &&
                   this.playerList.count() >= MIN_PLAYER_COUNT;
        },

        _getPlayerRole: function() {
            if (false === this.playerRole()) {
                return false;
            }

            return this.playerRole() === IS_SPY ? 'spy' : 'counter-spy';
        },

        onConnect: function() {
            this.isConnected(true);
        },

        onNewMaster: function(event, data) {
            this.isMaster(this.playerName() && data.player_name === this.playerName());
            if(this.isMaster()) {
                alert('You\'re the new master player. Only you can start the game.');
            }
        },

        onGameStarted: function() {
            this.isGameStarted(true);
            alert('The game has started');
        },

        onGameAborted: function() {
            this.isGameStarted(false);
            this.hasJoined(false);
            this.playerName('');
            this.isMaster(false);
            this.playerList().removeAll();

            alert('The game has been aborted');
        },

        onLostConnection: function() {
            alert('A player connection was lost.\
            Game will be aborted if connection is not resumed in 30s.');
        },

        join: function() {
            var self = this;

            $.post('/join', { player_name: this.playerName })
            .done(function(response) {
                if(!response.joined) {
                    return alert('Could not join game: ' + response.error || 'error unknown');
                }
                self.hasJoined(true);

                // Quit game when navigating away from the page
                $(window).on('beforeunload', self.onBeforeQuit.bind(self));
                $(window).on('unload', self.onQuitGame.bind(self));

                self.wsController.send({ playerName: self.playerName() });
            });
        },

        onRoleAssigned: function(event, data) {
            this.playerRole(data.role);
        },

        startGame: function() {
            $.post('/start', { player_name: this.playerName })
            .done(function(response) {
                if(!response.started) {
                    return alert('Could not start game: ' + response.error || 'error unknown');
                }
            });
        },

        onBeforeQuit: function() {
            if(this.hasJoined() > 0) {
                var msg = ['Navigating away from this page will make you quit the game.'];
                if(this.isGameStarted()) {
                    msg.push(' Since the game has already started, quitting is going to abort it. This will put everybody on edge for the rest of the day.');
                }
                return msg.join('');
            }
        },

        onQuitGame: function() {
            $.ajax({
                url: '/quit',
                method: 'post',
                async: false,
                data: { player_name: this.playerName }
            });
        }
    };

    wsController = new WebSocketController();
    playerList = new PlayerListViewModel(wsController);
    game = new PyLinq(playerList, wsController);

    ko.applyBindings(game);
    wsController.connect();

    window.wsController = wsController;
});