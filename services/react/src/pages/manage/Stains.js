import api from '../../API';
import styles from './Stains.module.css';
import { useLoaderData, } from 'react-router-dom';
import { useState } from 'react';
import CrudPanel from '../../widgets/CrudPanel';
import { readNested } from '../../helpers/assignfield';

function Stains(){
    const loaderData=useLoaderData()
    const [items, setItems] = useState(loaderData)
    const [schemas, setSchemas] = useState([]);
    const [selectedSchema, setSelectedSchema] = useState();

    const refreshSchemas = ()=>{
        api.get('/bdsa/schema',{query:{name:'slide'}}).then(d=>{
            setSchemas(d.data);
            setSelectedSchema(d.data[0]);
        })
    }

    function updateItems(isNew){
        setItems(arr=>isNew ? [...arr, isNew] : [...arr])
    }


    const opts = selectedSchema ? Object.values(selectedSchema.definition.properties.bdsa_stain_id.items.properties) : []
    
    
    

    function makeFields(item){
        const props = item.schema?.properties || [];        
        const schemaFields = Object.entries(props).map(([key, val])=>{
            const field = {...val}
            field.required = item.schema?.required?.includes(key) === true;
            field.key = `details.${key}`;
            field.body= `details.${key}`;
            return field;
        })

        const name = {title:'Name',type:'string',required:true,query:'name',key:'name'} // including 'query' tells the submit button to pass this in the query params, not the body, with the value as the key
        const usedFrom = {title:'Used from', type:'string',body:'used_from',key:'used_from'} // including 'body' tells the submit button to pass this in the body of the request
        const usedTo = {title:'Used until', type:'string',body:'used_to',key:'used_to'}
        const fields = [name, usedFrom, usedTo, ...schemaFields] // the schema fields will be passed in the details object in the body
        // for(const f of fields){
        //     if(f.key){
        //         // f.value = item[f.key]
        //         f.value = readNested(item, f.key)
        //     } 
        // }

        return fields;
    }

    console.log(
        'schema', selectedSchema
    )
    return(
        <>
        <h3>Manage Stains</h3>
        
        <label>Slide schema version:</label>
        <select onChange={ev => setSelectedSchema(schemas[ev.target.value])}>
            {schemas.map((s, index)=><option value={index} key={s._id}>{s.version}</option>)}
        </select> <button onClick={refreshSchemas}>Load/Refresh Slide Schemas</button>
        <div>
            {opts.length==0 && <span>Select a schema in order to define new stains</span>}
            {opts.length > 0 && <label>Add: </label>}
            {opts.length > 0 && opts.map((d) => <button onClick={()=>updateItems({schema:d})} key={d.title}>{d.title}</button>)}
        </div>
        
        <div>
            {items.map((item,index)=>{
                const bodyParams = {
                    schema: item.schema,
                    schema_id: item.schemaId || selectedSchema._id
                }
                const queryParams = {
                    id:item._id,
                }
                return <CrudPanel url={'bdsa/stain'} 
                           remove={()=>{items.splice(index, 1); updateItems();}} 
                           fields={makeFields(item)}
                           titleField={'name'} 
                           key={item._id || `stain-panel-${index}`}
                           id={item._id}
                           item={item}
                           bodyParams={bodyParams}
                           queryParams={queryParams}>
                </CrudPanel>
                }
            )}
        </div>
        </>
    )
}

async function Loader(){
    
    const response = await api.get('bdsa/stain');
    // console.log('loader data response', response)
    if(!response.status=='200'){
        throw new Error("Failed to fetch data from the BDSA")
    } else {
        return response.data;
    }
}

export default Stains
export { Loader }