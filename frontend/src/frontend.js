
var initFrontend = function(serverList, currentServer) {
    window.app = new Vue({
        el: '#app',
        data: {
          serverId: currentServer,
          serverList: servers,
          loading: true,
          creating: false,
          entries: [],
          entryRequest: null,
          entryText: ''
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
                }).fail(function( jqxhr, textStatus, error ) {
                    if (error != "abort") {
                        setTimeout(function(){
                            vm.reloadBoard();
                        }, 1000)
                    }
                });
            }, 
            createEntry: function() {

                if (this.creating) {
                    return; // wait for the previous request
                }

                console.debug("Adding entry for " + this.serverId);
                
                this.creating = true;
                var vm = this;

                this.entryRequest = $.post( 'http://' + vm.serverList[vm.serverId-1] + '/entries',
                {
                    text: vm.entryText
                },
                function( data ) {
                    vm.creating = false;
                    vm.reloadBoard();
                });
            }
        }
    });
};