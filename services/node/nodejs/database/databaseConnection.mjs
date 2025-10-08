import mongoose from 'mongoose';

const {
  MONGO_USERNAME,
  MONGO_PASSWORD,
  MONGO_HOSTNAME,
  MONGO_PORT,
  MONGO_DB,
} = process.env;

const options = {
    useNewUrlParser: true,
    useUnifiedTopology: true,
    useFindAndModify:false,
  };
const url = `mongodb://${MONGO_HOSTNAME}:${MONGO_PORT}`;

const connection = mongoose.createConnection(url, options);
connection.once('open', function(){
    console.log('MongoDB is connected');
});
connection.once('error', function(err){
    console.log('MongoDB error',err);
});

export default function(app) {
    let promises=[
        new Promise((resolve,reject)=>{
            connection.once('open', function() {
                // All OK - fire (emit) a ready event. 
                resolve();
            });
        }),
        
    ];
    Promise.all(promises).then(()=>app.emit('ready'));
    
    
}