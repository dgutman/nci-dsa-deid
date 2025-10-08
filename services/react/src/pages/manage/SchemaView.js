import api from '../../API';
import { useLoaderData, useParams, useRevalidator } from 'react-router-dom';
import { useState } from 'react';
import { JsonEditor } from 'json-edit-react';

function SchemaView(){

    // function handleSubmit(event){
    //     event.preventDefault();
    //     const data = Object.fromEntries(new FormData(event.target));
    //     console.log('Submitting', data);
    //     api.put('bdsa/network/local', {query: data})
    // }

    const {name} = useParams();
    const revalidator = useRevalidator();
    // The loader will access current definitions
    const loaded = useLoaderData() || [];
    // console.log('loader data', xxx)
    
    const data = loaded.sort((a, b)=> b.version - a.version); 
    const [def, setDef] = useState();
    const [index, setIndex] = useState(0)

    function saveChanges(){
        console.log('saving',def);
        api.post('bdsa/schema', {query:{name}, body:{definition: def}}).then(d=>{
            console.log('after saving', d)
            revalidator.revalidate()
        })
    }
    function updateDefinition(updated){
        data[index].definition = updated;
        setDef(updated);
    }
    if(index>=0){
        return (
            <>
            <button onClick={()=>console.log('testing',def || data[index].definition)}>Test</button>
            <h3>Schema: {name}</h3>
            <label>Version:</label>
            <select onChange={ev=>{setIndex(ev.target.value); setDef(); }}>
                {data.map( (d,index) => <option key={index} value={index}>{d.version}</option>)}
            </select>
            <div>
                Definition:
                <button disabled={!def} style={{marginLeft:'3em'}} onClick={saveChanges}>Save (will create a new version)</button>
            </div>
            <JsonEditor data={data[index].definition} setData={updateDefinition}></JsonEditor>
            
            </>
        )
    } else {
        return <div>Loading...</div>
    }

    
}

async function Loader({params}){
    const {name} = params
    console.log('In loader', name)
    if(!name){
        return [];
    }
    const response = await api.get('bdsa/schema',{query:{name:name}});
    // console.log('loader data response', response)
    if(!response.status=='200'){
        throw new Error("Failed to fetch data from the BDSA")
    } else {
        return response.data;
    }
}

export default SchemaView;
export { Loader };