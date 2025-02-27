const axios = require('axios');

async function sendPing(account) {
    try {
        const response = await axios.get(
            'https://nodego.ai/api/user/me',  // Endpoint correcto
            {
                headers: {
                    'Authorization': `Bearer ${account.token}`,
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Encoding': 'gzip, deflate, br, zstd',
                    'Accept-Language': 'en-GB,en;q=0.9,es-ES;q=0.8,es;q=0.7',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
                    'Sec-Ch-Ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Windows"',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Referer': 'https://nodego.ai/',
                    'Origin': 'https://nodego.ai/'
                }
            }
        );

        if (response.status === 200) {
            console.log(`[✔] Ping exitoso para ${account.token.substring(0, 6)}...`);
        } else {
            console.error(`[✖] Error en ping para ${account.token.substring(0, 6)}:`, response.data);
        }
    } catch (error) {
        console.error(`[✖] Fallo en la solicitud de ping:`, error.message);
    }
}

module.exports = { sendPing };
