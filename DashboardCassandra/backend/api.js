const express = require('express');
const router = express.Router();
const client = require('./db');

router.get('/:keyspaceValue/:nazovTabulkyValue/:channelNameValue/:typSignaluValue', async (req, res) => {
    const { keyspaceValue, nazovTabulkyValue, channelNameValue, typSignaluValue } = req.params;

    try {
        const query = `SELECT * FROM ${keyspaceValue}.${nazovTabulkyValue} WHERE channel=${channelNameValue} AND eeg_wave='${typSignaluValue}' ALLOW FILTERING`;
        const result = await client.execute(query);
        res.json(result.rows);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Server error' });
    }
});
router.get('/:keyspaceValue/:nazovTabulkyValue/:channelNameValue', async (req, res) => {
    const { keyspaceValue, nazovTabulkyValue, channelNameValue } = req.params;

    try {
        const query = `SELECT * FROM ${keyspaceValue}.${nazovTabulkyValue} WHERE channel=${channelNameValue}`;
        const result = await client.execute(query);
        res.json(result.rows);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Server error' });
    }
});
module.exports = router;