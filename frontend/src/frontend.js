
var initFrontend = function(serverList, currentServer) {
    window.app = new Vue({
        el: '#app',
        data: {
          serverId: currentServer,
          serverList: servers,
          loading: true,
          entries: [],
          entryRequest: null
        },
        created: function() {
            this.changeServer(currentServer);
        },
        methods: {
            changeServer: function() {
                console.debug("Changed server to " + this.serverId);
                this.reloadBoard();
            },

            setBoardEntries: function(entries) {
                this.loading = false;
                this.entries = entries;
            },
            reloadBoard: function() {
                if (this.entryRequest != null) {
                    this.entryRequest.abort();
                }

                console.debug("Reloading board for " + this.serverId);
                
                this.loading = true;
                var vm = this;
                
                this.entryRequest = $.getJSON( 'http://' + vm.serverList[vm.serverId-1] + '/entries', function( data ) {
                    vm.setBoardEntries(data.entries);
                });
            }
        }
    });
};