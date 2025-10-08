import style from './Upload.module.css'
import { useState } from 'react';
// import { }

const Upload = function(){
    const [ files, setFiles ] = useState([]);
    

    return (
        <>
        <input type="file" multiple={true} onChange={(ev)=>{console.log(ev.target.files); setFiles([])}}></input>
        </>
    )
}

export default Upload;