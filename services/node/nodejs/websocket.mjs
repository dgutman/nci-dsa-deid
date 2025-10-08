import WebSocket, { WebSocketServer } from 'ws';


class WSServer{
    constructor(){
        this.server = new WebSocketServer({ noServer: true });

        // handle new connections
        this.server.on('connection', (ws, url) => {
            // parse the channel name out of the url. It will be the last string in the url.
            ws.channel = url.split('/').slice(-1)[0];
            
            // add a guid to the channel
            ws.guid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g,function(c) {
                let r = Math.random() * 16|0;
                let v = c == 'x' ? r : (r&0x3|0x8);
                return v.toString(16);
            });

            // flag the connection as alive
            ws.isAlive = true;

            // when the client sends a "pong" event, mark as alive
            ws.on('pong',()=>{
              ws.isAlive = true;
            })

            //connection is up, add a handler to parse 
            ws.on('message', (message) => {
                try{
                    const parsed = JSON.parse(message);
                    console.log(ws.channel + `${(' '+parsed.target) || ''}: ` + parsed.message);
                    this.broadcast(ws, parsed.message, parsed.target);
                } catch(e){
                    console.log('Websocket error', e);
                    this.send(ws, 'There was a problem with your message. ' + e);
                }
            });
          
            //send immediatly a feedback to the incoming connection    
            this.send(ws, 'Hi there, I am a WebSocket server. Your ID is ' + ws.guid, true);
            this.broadcast(ws, {action: 'join', guid: ws.guid} );
        });

        // periodically terminate connections that have died
        setInterval(() => {
            this.server.clients.forEach((ws) => {
                
                if (!ws.isAlive) return ws.terminate();
                
                ws.isAlive = false;
                ws.ping();
            });
        }, 10000);
    }
    setHTTPServer(server){
        server.on('upgrade', (req, socket, head) => {
            this.server.handleUpgrade(req, socket, head, (ws) => {
                this.server.emit('connection', ws, req.url)
            })
        })
    }
    send(ws, message, sender){
        const payload = JSON.stringify({
            message:message,
            sender: sender ? sender.guid : 'server'
        });
        ws.send(payload);
    }
    broadcast(sender, message, target){
        // console.log('clients', this.server.clients);
        // console.log('')
        const targets = Array.from(this.server.clients).filter(ws => ws.channel === sender.channel && ws !== sender && (target ? ws.guid === target : true));
        targets.forEach(ws => this.send(ws, message, sender));
    }
    channelExists(channel){
        return Array.from(this.server.clients).some(client => client.channel === channel); 
    }
}


const wsServer = new WSServer();

export { wsServer }