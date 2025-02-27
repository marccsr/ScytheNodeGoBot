const fs = require('fs');

function loadAccounts() {
    const dataFile = 'data.txt';
    if (!fs.existsSync(dataFile)) {
        console.error(`[✖] No se encontró el archivo ${dataFile}`);
        process.exit(1);
    }

    const tokens = fs.readFileSync(dataFile, 'utf-8')
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0);

    return tokens.map(token => ({ token }));
}

module.exports = { loadAccounts }; // Exportación correcta como objeto
