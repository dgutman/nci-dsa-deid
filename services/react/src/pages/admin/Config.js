import api from '../../API';
import styles from './Config.module.css';
import { useLoaderData } from 'react-router-dom';
import { useState } from 'react';

function Config(){

    function handleSubmit(event){
        event.preventDefault();
        const data = Object.fromEntries(new FormData(event.target));
        console.log('Submitting', data);
        api.put('bdsa/network/local', {query: data})
    }

    // The loader will access current settings 
    const loaded = useLoaderData();
    const data = {};
    if(loaded.status === 200){
        Object.assign(data, loaded.data);
    } else {
        throw new Error({message:'There was an error fetching data from the DSA', error: loaded});
    }
    console.log(data)
    return (
        <>
        <h1>BDSA Config</h1>
        <form onSubmit = {handleSubmit} className={styles.form}>
            <div className={styles.inputs}>
                <label>Display name:<input name='displayName' type='text' placeholder='The name of this BDSA' defaultValue={data.displayName} required/> </label>
                <label>API URL: <input name='apiUrl' type='text' placeholder='The public-facing URL for the API' defaultValue={data.apiUrl} required/></label>
                <label>Contact name: <input name='contactName' type='text' placeholder='Conctact name' defaultValue={data.contactName}/></label>
                <label>Contact email: <input name='contactEmail' type='text' placeholder='Contact email' defaultValue={data.contactEmail}/></label>
            </div>
            <input type='submit' value='Save changes'/>
        </form>
        </>
    )
}

function Loader(){
    return api.get('bdsa/network/local');
}

export default Config;
export { Loader };