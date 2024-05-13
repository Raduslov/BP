

const express = require('express');
const cors = require('cors');
const apiRouter = require('./api');


const app = express();

app.use(cors());
app.use(express.json());

app.use('/api', apiRouter);

const PORT = process.env.PORT || 3002;
app.listen(PORT, () => {
    console.log(`Server bezi na portu ${PORT}`);
});
