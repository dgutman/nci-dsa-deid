import api from '../API';
import styles from './CrudPanel.module.css';
import { useState, useReducer } from 'react';
import { readNested, assignNested } from '../helpers/assignfield';
import { getMultiselectValues } from '../helpers/multiselect';


const DataEntry = ({schema, labelWidth})=>{
    // console.log('DataEntry',schema)
    const placeholder=schema.examples?`e.g. ${schema.examples.join(', ')}`:''
    const [val, setVal] = useState(typeof schema.value !== 'undefined' ? schema.value : '');
    const [message, setMessage] = useState(schema.type=='array'?schema.value:'');
    const re = schema.pattern ? new RegExp(schema.pattern) : undefined;
    const invalid = schema.pattern && val && !re.test(val);
    const missing = schema.required && !val && !schema.enum;
    const typecheck = ['string', 'array', 'integer','file','files'].includes(schema.type)
    const labelStyle = {width:labelWidth}
    function listFiles(t){
        console.log('listFiles', t.files)
    }
    return (
        <>
        <div className={styles['data-entry']}>
            <label style={labelStyle} title={schema.required?"Required":""}>{schema.title}{schema.required && <span className={styles.required}>*</span>}:</label>
            <div>
                {!typecheck && <span>Field type "{schema.type}" is not supported at this time.</span> }
                {schema.type==='string' && !schema.enum &&
                    <input name={schema.title}
                            placeholder={placeholder}
                            onInput={ev=>setVal(ev.target.value)} 
                            value={val} 
                            required={schema.required}></input> }
                {schema.type==='integer' && !schema.enum &&
                    <input name={schema.title}
                            type="number"
                            placeholder={placeholder}
                            onInput={ev=>setVal(ev.target.value)} 
                            value={val} 
                            required={schema.required}></input> }
                {schema.enum && schema.type=='string' && 
                    <select name={schema.title} defaultValue={val}>
                        <option disabled value=''>--select an option--</option>
                        {schema.enum.map(e=> <option key={e} val={e}>{e}</option>)}
                    </select> }
                {schema.enum && schema.type=='integer' && 
                    <select name={schema.title} defaultValue={val}>
                        <option disabled value=''>--select an option--</option>
                        {schema.enum.map(e=> {
                            const re = new RegExp(`${e}\\s*=\\s*([^\\.,;]*)`);
                            // const match = re.test(schema.description);
                            const match = schema.description.match(re)
                            const text = match ? match[1] : e;
                            if(!match) console.log('No match', e, schema.description, `${e}\\s*=\\s*([^\\.,;]*)`)
                            return (<option key={e} val={e}>{text}</option>)
                        })}
                    </select> }
                {schema.enum && schema.type==='array' && 
                    <select name={schema.title} multiple onChange={ev=>setMessage(getMultiselectValues(ev.target))}>
                        {schema.enum.map(e=> <option key={e} val={e} selected={val.includes(e)}>{e}</option>)}
                    </select> }
                {schema.type==='files' && 
                    <input name={schema.title} type="file" multiple onChange={ev=>listFiles(ev.target)}/>}
                {schema.type==='file' && 
                    <input name={schema.title} type="file"/>}
            </div>
            <div>
                {message && <span className={styles.valuemessage}>{Array.isArray(message) ? message.join(', ') : message}</span>}
                {invalid && <span className={styles.invalid}>Does not match required pattern. See schema for details.</span>}
                {missing && <span className={styles.invalid}>A value is required.</span>}
            </div>
            
        </div>
        </>
    )
}

const CrudPanel = ({id, remove, onSave, item, url, fields, titleField, fixed, bodyParams, queryParams})=>{
    // console.log('schema', data, data.schema, data.schema.properties)
    
    const [_id, setId] = useState(id);
    const [panelExpanded, setPanelExpanded] = useState(fixed || !id);//start existing items as collapsed
    const [editingEnabled, setEditingEnabled] = useState(!id)
    const [schemaExpanded, setSchemaExpanded] = useState(false);
    const [updateKey, forceUpdate] = useState(x=>x+1);
    const [valid, setValid] = useState(true);
    const [saveResponse, setSaveResponse] = useState();
    const [deleteFailed, setDeleteFailed] = useState(false);
    const [itemName, setItemName] = useState(item[titleField])

    if(item){
        for(const f of fields){
            if(f.key){
                // f.value = item[f.key]
                f.value = readNested(item, f.key)
            } 
        }
    }

    let validationFailed = false;

    function getValue(target, getter){
        if(getter){
            return getter(target)
        } else {
            return target.multiple? getMultiselectValues(target) : target.value
        }
    }
    
    function onSubmit(event){
        event.preventDefault();

        // iterate over the fields, validating them and building the json object to submit
        for(const f of fields){
            const target=event.target[f.title];
            const val = getValue(target, f.getValue)
            // const val = event.target[f.title].value;
            if(f.query){
                queryParams[f.query] = val;
            } else if(f.body){
                // bodyParams[f.body]=val;
                assignNested(bodyParams, f.body, val)
            }
            else {
                // this field will not be saved, as it is not sent in either the query or the body parameters
                console.warn(`The field titled "${f.title}" does not have a key for query or body parameters, and will not be saved`, f);
            }
            
            // console.log(f.title, f.pattern)
            if(val && f.pattern){
                const re = new RegExp(f.pattern)
                if(!re.test(val)){
                    setValid(false);
                    validationFailed = true;
                }
            }
            if (f.required && !val){
                setValid(false);
                validationFailed = true;
            } 
        }
        if(!validationFailed){
            // console.log('Submit the values here, then clear the form');
            if(_id){
                // console.log('Putting changes')
                api.put(url, {query: queryParams, body: bodyParams}).then(d=>{
                    if(d.status===200){
                        setSaveResponse(true);
                        setItemName(d.data[titleField]);
                        setTimeout(()=>setSaveResponse(), 10000);
                        if(onSave){
                            onSave(d.data)
                        }
                    } else {
                        setSaveResponse(false);
                    }
                })
            } else {
                api.post(url, {query: queryParams, body: bodyParams}).then(d=>{
                    if(d.status===200){
                        setSaveResponse(true);
                        setId(d.data._id);
                        queryParams.id = d.data._id;
                        setItemName(d.data[titleField]);
                        setTimeout(()=>setSaveResponse(), 10000)
                        if(onSave){
                            onSave(d.data)
                        }
                    } else {
                        setSaveResponse(false);
                    }
                })
            }
        } 
    }

    function deleteItem(){
        api.delete(url,{query:{'id':_id}}).then(d=>{
            if(d.status===200){
                remove();
            } else {
                setDeleteFailed(true);
            }
        })
        
    }
    
    function reset(){
        forceUpdate()
    }
    
    return(
        <>
        <div className={`${styles['crud-panel']} ${fixed ? styles['fixed-panel']:''}`}>
            {!fixed && <h3>{panelExpanded ? <button type='button' onClick={()=>setPanelExpanded(false)}>-</button>:<button type='button' onClick={()=>setPanelExpanded(true)}>+</button>}
                {itemName || 'Creating: ' + item.schema.title}
                <span className={styles['schema-info']}>{item.schema.title&&'Schema type:'} {item.schema.title}</span>
            </h3>}
            {panelExpanded && <button onClick={()=>setEditingEnabled(true)} disabled={editingEnabled}>Edit</button>}
            {panelExpanded && <form onSubmit={onSubmit}><fieldset disabled={!editingEnabled} >
                <div className={styles.fieldList}>
                {/* {fields.map((f,i) => <DataEntry schema={f} value={f.value} key={f.title+i+updateKey} onChange={ev=>{f.value=ev.target.value;}}></DataEntry>)} */}
                {fields.map((f,i) => <DataEntry schema={f} value={f.value} key={f.title+i+updateKey} ></DataEntry>)}
                
                <div className={styles.schema}>
                    <button type='button' onClick={()=>setSchemaExpanded(e => !e)}>{schemaExpanded ? 'Hide' : 'Show'} schema</button>
                    {schemaExpanded && <pre>{JSON.stringify(item.schema, null, 2)}</pre>}
                </div>
                {/* <JsonEditor data={data.def} setData={updateDefinition}></JsonEditor> */}
                </div>
                <button type='submit'>Save</button>
                {!_id && <button type="button" onClick={()=>reset()}>Reset</button>}
                {!_id && <button type="button" onClick={()=>{reset();setEditingEnabled(false)}}>Cancel</button>}
                {_id && <button type="button" onClick={deleteItem}>Delete</button>}
                {typeof saveResponse !== 'undefined' && (saveResponse ? <span className={styles.valid}>Save was successful</span>:<span className={styles.invalid}>Save failed</span>)}
                {!valid && <span className={styles.invalid}>Validation failed</span>}
                {deleteFailed && <span className={styles.invalid}>Error: there was a problem deleting this item.</span>}
                </fieldset>
                </form>
            }
        </div>
        </>
    )
}

export default CrudPanel
export { DataEntry }
