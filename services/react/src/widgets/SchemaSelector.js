import api from '../API';
import styles from './SchemaSelector.module.css';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

const SchemaSelector = ({schemaName, onSelect, immediate})=>{
    // const { isPending, isError, data: response, error } = useQuery({ queryKey: ['immediate'], queryFn: () => api.get('bdsa/schema',{query:{name:schemaName}}) });
    const [schemas, setSchemas] = useState([]);
    // const [selectedSchema, setSelectedSchema] = useState();
    const setSelectedSchema = onSelect;


    const refreshSchemas = ()=>{
        api.get('/bdsa/schema',{query:{name:schemaName}}).then(d=>{
            if(d.status==200){
                setSchemas(d.data);
                setSelectedSchema(d.data[d.data.length-1]);
            } else {
                console.warn('oops')
            }
            
        })
    }

    if(immediate){
        // if(response.status==200){
        //     setSchemas(response.data);
        //     setSelectedSchema(response.data[response.data.length-1]);
        // } else {
        //     console.warn(response)
        // }
    }

    if(!schemaName){
        return (<><div className={styles.errorMessage}>SchemaSelector: missing required parameter `schemaName`</div></>)
    }
    if(!onSelect){
        return (<><div className={styles.errorMessage}>SchemaSelector: missing required parameter `onSelect`</div></>)
    }


    return (<>
        <label>Schema version:</label>
        <select onChange={ev => setSelectedSchema(schemas[ev.target.value])}>
            {schemas.map((s, index)=><option value={index} key={s._id}>{s.version}</option>)}
        </select> <button onClick={refreshSchemas}>Load/Refresh Slide Schemas</button>
    </>)
}

export default SchemaSelector;