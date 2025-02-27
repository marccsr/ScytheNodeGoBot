import fs from 'fs';
import axios from 'axios';
import { URL } from 'url';
import { SocksProxyAgent } from 'socks-proxy-agent';
import { HttpsProxyAgent } from 'https-proxy-agent';
import { HttpProxyAgent } from 'http-proxy-agent';
import chalk from 'chalk';
import displayBanner from './banner.js';

class ScytheNodeGo {
    constructor(token, proxyUrl = null) {
        this.apiBaseUrl = 'https://nodego.ai/api';
        this.bearerToken = token;
        this.agent = proxyUrl ? this.createProxyAgent(proxyUrl) : null;
    }

    createProxyAgent(proxyUrl) {
        try {
            const parsedUrl = new URL(proxyUrl);
            if (proxyUrl.startsWith('socks')) {
                return new SocksProxyAgent(parsedUrl);
            } else if (proxyUrl.startsWith('http')) {
                return {
                    httpAgent: new HttpProxyAgent(parsedUrl),
                    httpsAgent: new HttpsProxyAgent(parsedUrl)
                };
            } else {
                const httpUrl = `http://${proxyUrl}`;
                const httpParsedUrl = new URL(httpUrl);
                return {
                    httpAgent: new HttpProxyAgent(httpParsedUrl),
                    httpsAgent: new HttpsProxyAgent(httpParsedUrl)
                };
            }
        } catch (error) {
            console.error(chalk.red('Invalid proxy URL:'), error.message);
            return null;
        }
    }

    async makeRequest(method, endpoint, data = null) {
        const config = {
            method,
            url: `${this.apiBaseUrl}${endpoint}`,
            headers: {
                'Authorization': `Bearer ${this.bearerToken}`,
                'Content-Type': 'application/json',
                'Accept': '*/*'
            },
            ...(data && { data }),
            timeout: 30000
        };

        if (this.agent) {
            if (this.agent.httpAgent) {
                config.httpAgent = this.agent.httpAgent;
                config.httpsAgent = this.agent.httpsAgent;
            } else {
                config.httpAgent = this.agent;
                config.httpsAgent = this.agent;
            }
        }

        try {
            return await axios(config);
        } catch (error) {
            if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
                throw new Error(`Proxy connection failed: ${error.message}`);
            }
            throw error;
        }
    }

    async ping() {
        try {
            const response = await this.makeRequest('POST', '/user/nodes/ping', { type: 'extension' });
            return {
                statusCode: response.data.statusCode,
                message: response.data.message,
                metadataId: response.data.metadata.id
            };
        } catch (error) {
            console.error(chalk.red(`Ping failed: ${error.message}`));
            throw error;
        }
    }
}

class MultiAccountPinger {
    constructor() {
        this.accounts = this.loadAccounts();
        this.isRunning = true;
    }

    loadAccounts() {
        try {
            const accountData = fs.readFileSync('data.txt', 'utf8')
                .split('\n')
                .filter(line => line.trim());
            const proxyData = fs.existsSync('proxies.txt')
                ? fs.readFileSync('proxies.txt', 'utf8')
                    .split('\n')
                    .filter(line => line.trim())
                : [];
            return accountData.map((token, index) => ({
                token: token.trim(),
                proxy: proxyData[index] || null
            }));
        } catch (error) {
            console.error(chalk.red('Error reading accounts:'), error);
            process.exit(1);
        }
    }

    async processPing(account) {
        const pinger = new ScytheNodeGo(account.token, account.proxy);
        try {
            const pingResponse = await pinger.ping();
            console.log(chalk.green(`Ping Status:`));
            console.log(chalk.green(`  Status: ${pingResponse.statusCode}`));
            console.log(chalk.green(`  Message: ${pingResponse.message}`));
        } catch (error) {
            console.error(chalk.red(`Error pinging account: ${error.message}`));
        }
    }

    async runPinger() {
        displayBanner();
        process.on('SIGINT', () => {
            console.log(chalk.yellow('\nGracefully shutting down...'));
            this.isRunning = false;
            setTimeout(() => process.exit(0), 1000);
        });

        console.log(chalk.yellow('\n⚡ Starting regular ping cycle...'));
        while (this.isRunning) {
            console.log(chalk.white(`\n⏰ Ping Cycle at ${new Date().toLocaleString()}`));
            for (const account of this.accounts) {
                if (!this.isRunning) break;
                await this.processPing(account);
            }
            if (this.isRunning) {
                console.log(chalk.gray('\nWaiting 15 seconds before next cycle...'));
                await new Promise(resolve => setTimeout(resolve, 15000));
            }
        }
    }
}

const multiPinger = new MultiAccountPinger();
multiPinger.runPinger();
