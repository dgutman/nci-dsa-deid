import api from '../../API';
import { useLoaderData } from 'react-router-dom';
import { useState } from 'react';
import WsiCard from '../../widgets/WsiCard';

function View(){

    // The loader will access current settings 
    const loaded = useLoaderData();
    // const data = {};
    if(loaded.ok){
        return (
            <>
            <h1>BDSA Slides</h1>
            <div id='all-slides'>
                {loaded.data.map(WsiCard)}
                {/* TODO: make slide list
                <div>
                    <pre>{JSON.stringify(loaded.data,null,2)}</pre>
                </div> */}
            </div>
            </>
        )
    } else {
        return (
            <>
            <h1>Oops, there was a problem</h1>
            <p>{loaded.error}</p>
            <button onClick={()=>window.location.reload()}>Reload after logging in</button>
            </>
        )
    }
    
}

/**
 * 
 * @returns Object the with fields "ok", "data" and "error" 
 */
function Loader(){
    return api.get('resource/lookup',{query: {path: '/collection/Bdsa/All Slides'}}).then(d => {
        if(d.status=200){
            if(d.data._id){
                return api.get('item', {query: {folderId: d.data._id}}).then(d=>{
                    return {ok: true, data: d.data};
                })
            } else {
                return {
                    ok: false,
                    data: null,
                    error: 'A folder named "All Slides" was not found with the BDSA collection. You must be logged in and the folder must exist in the DSA.'
                }
            }
            
        } else {
            return {
                ok: false,
                data: null,
                error: 'There was a problem contacting the DSA server.'
            }
        }
    });
}

export default View;
export { Loader };