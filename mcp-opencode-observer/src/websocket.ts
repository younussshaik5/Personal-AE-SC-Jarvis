import { WebSocketServer } from 'ws';

interface WebSocketClient {
  ws: any;
  subscriptions: string[];
}

export class LiveUpdateServer {
  private wss: any;
  private clients: Set<WebSocketClient> = new Set();
  private db: any;
  private port: number;

  constructor(db: any, port: number) {
    this.db = db;
    this.port = port;
  }

  start(server: any): void {
    this.wss = new WebSocketServer({ server });

    this.wss.on('connection', (ws: any) => {
      const client: WebSocketClient = {
        ws,
        subscriptions: []
      };
      this.clients.add(client);

      ws.on('message', (message: string) => {
        try {
          const data = JSON.parse(message);
          this.handleMessage(client, data);
        } catch (error) {
          ws.send(JSON.stringify({ type: 'error', message: 'Invalid JSON' }));
        }
      });

      ws.on('close', () => {
        this.clients.delete(client);
      });

      ws.send(JSON.stringify({
        type: 'connected',
        message: 'Connected to OpenCode Observer WebSocket'
      }));
    });
  }

  private handleMessage(client: WebSocketClient, data: any): void {
    switch (data.action) {
      case 'subscribe':
        if (data.channel && !client.subscriptions.includes(data.channel)) {
          client.subscriptions.push(data.channel);
          client.ws.send(JSON.stringify({
            type: 'subscribed',
            channel: data.channel
          }));
        }
        break;

      case 'unsubscribe':
        client.subscriptions = client.subscriptions.filter(s => s !== data.channel);
        break;

      case 'ping':
        client.ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
        break;
    }
  }

  broadcast(type: string, data: any, channel?: string): void {
    const message = JSON.stringify({ type, data, timestamp: Date.now(), channel });

    for (const client of this.clients) {
      if (!channel || client.subscriptions.includes(channel)) {
        if (client.ws.readyState === 1) {
          client.ws.send(message);
        }
      }
    }
  }

  getClientCount(): number {
    return this.clients.size;
  }
}