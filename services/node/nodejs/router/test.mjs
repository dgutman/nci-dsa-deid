import * as express from 'express';

const router = express.Router();

export default router;


router.get("/", function(req, res){
    res.send('Test test test');
});

router.get("/:name", function(req, res){
    res.send(`Unknown endpoint ${req.params.name}`);
});

