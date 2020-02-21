
var initFrontend = function(numServers, fromPort, currentServer) {

    var servers = [];
    var i;
    for (i = 1; i <= numServers; i++) {
        servers.push(i);
    }

    window.app = new Vue({
        el: '#app',
        data: {
          server: currentServer,
          servers: servers,
          loading: true,
          entries: [],
          entryRequest: null
        },
        created: function() {
            this.changeServer(currentServer);
        },
        methods: {
            changeServer: function() {
                console.debug("Changed server to " + this.server);
                this.reloadBoard();
            },
            reloadBoard: function() {
                if (this.entryRequest != null) {
                    clearTimeout(this.entryRequest);
                    timer = setTimeout(()=>{ this.show = false; }, 3000);
                }

                this.loading = true;
                
                this.entryRequest = setTimeout(() => { this.loading = false;
                    this.entries.push("Test13"); }, 500);
                
            }
        }
    });
};