import api from '../API.js';
import { useState } from 'react';

function APITest(){

    const [response, setResponse] = useState("");

    const call = (event)=>{
        event.preventDefault();
        console.log(event);
        const data = Object.fromEntries(new FormData(event.target));
        
        console.log(data);


        api.fetch(data.queryString, data.responseType).then(output => {
            console.log(output);
            setResponse(output);
        } );
    }
    return (
        <>
        <div style={{margin:'0 auto', maxWidth:'960px'}}>
            <div style={{margin:'0 auto', maxWidth:'960px'}}>
                <h2>Test the girder API here</h2>
                <form onSubmit={call}>
                    <input name="queryString" placeholder="queryString"></input><br></br>
                    <textarea name="opts" placeholder="options"></textarea><br></br>
                    <input name="responseType" placeholder="text or json"></input><br></br>
                    <input type="submit"/>
                </form>
            </div>
            <div>
                <h3>Output:</h3>
                <pre>{JSON.stringify(response, null, 2)}</pre>
            </div>
        </div>
        
        </>
    )
}

export default APITest