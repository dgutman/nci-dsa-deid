import api from '../../API';
import styles from './Case.module.css';
import { useState } from 'react';
import { readNested } from '../../helpers/assignfield';
import { DataEntry } from '../../widgets/CrudPanel';
import SchemaSelector from '../../widgets/SchemaSelector';
import CrudPanel from '../../widgets/CrudPanel';
import { json, useLoaderData, Link } from 'react-router-dom';
import StainBlockSchemaPicker from '../../widgets/StainBlockSchemaPicker';

const CasePanel = ({onDelete, onSave, schema, item, pickSlides}) => {

    if(item){
        schema = {definition: item.schema};
    }
    
    const fields = [
        {title:'Local case ID', type:'string', key: 'localId', body:'localId', required:true},
        ...Object.entries(schema.definition.properties).map(([key,val])=>{
            val.key = `details.${key}`;
            val.body = `details.${key}`;
            if(val.type=='number') val.type='integer';
            return val;
        }),
    ]

    if(pickSlides){
        fields.push(
            {title:'WSI file names', type:'files', key:'slides', body:'slides', getValue:t=>{
                console.log('getValue', t, Array.from(t.files).map(f=>f.name))
                return Array.from(t.files).map(f=>f.name);
            }}
        )
    }

    const bodyParams = {
        schema: item?.schema || schema.definition,
        schema_id: item?.schemaId || schema._id
    }
    const queryParams = {
        id:item?._id,
    }


    return(<>
        <CrudPanel url={'bdsa/case'} 
                    remove={onDelete}
                    onSave={onSave} 
                    fields={fields}
                    titleField={'caseId'} 
                    key={item?._id}
                    id={item?._id}
                    item={item || {schema:schema.definition}}
                    fixed={true}
                    bodyParams={bodyParams}
                    queryParams={queryParams}>
        </CrudPanel>
    </>)

}

const ItemView = ({item, stainSchema, blockSchema, remove}) => {
    function deleteItem(){
        api.delete(`/item/${item._id}`).then(d=>{
            if(d.status===200){
                remove(item)
            }
        })
    }
    function onStainChange(stain){
        console.log('stain change', stain)
        api.put(`/item/${item._id}/metadata`,{json:{'stain':stain}})
    }
    function onBlockChange(block){
        console.log('block change', block)
        api.put(`/item/${item._id}/metadata`,{json:{'block':block}})
    }
    return (<>
        <div className={styles.itemview}>
            <div>{item.name}</div>
            <StainBlockSchemaPicker stainSchema={stainSchema} 
                     blockSchema={blockSchema} 
                     onStainChange={onStainChange} 
                     onBlockChange={onBlockChange}
                     stainVal = {item.meta.stain}
                     blockVal = {item.meta.block}></StainBlockSchemaPicker>
            <div>
                {!item.largeImage && <span className={styles.awaitingUpload}>Awaiting upload</span>}
                {item.largeImage && item.bdsaInQuarantine && <span className={styles.quarantined}>Quarantined</span>}
                {item.largeImage && !item.bdsaInQuarantine && <Link to={`/item/${item._id}`} className={styles.itemlink}>View item</Link>}
            </div> 
            <button onClick={deleteItem}>Delete</button>
        </div>
    </>)
}
const FileView = ({file, stainSchema, blockSchema, remove}) => {
    return (<>
        <div className={styles.fileview}>
            <div><button onClick={()=>remove(file.name)}>x</button> {file.name}</div>
            <StainBlockSchemaPicker stainSchema={stainSchema} blockSchema={blockSchema} onStainChange={s=>file.stain=s} onBlockChange={b=>file.block=b}></StainBlockSchemaPicker>
        </div>
    </>)
}

const SlidesPanel = ({doc, setDoc, stainSchema, blockSchema})=> {
    console.log('Rendering SlidesPanel', doc)

    const [files, setFiles] = useState({})
    const items = doc.items;
    
    function updateFiles(event){
        [...event.target.files].forEach(file=>{
            if(!files[file.name]){
                files[file.name] = file;
            }
        });
        setFiles({...files});
        event.target.value = '';
    }
    function removeFile(name){
        delete files[name];
        setFiles({...files})
    }
    function saveFiles(event){
        console.log('saving:', files)
        event.target.disabled = true;
        const filelist = Object.values(files).map(f=>{
            return {
                name:f.name,
                block: f.block,
                stain: f.stain
            }
        })
        api.post('/bdsa/case/files',{query:{id:doc._id},body:{files:filelist}}).then(resp=>{
            if(resp.status===200){
                setFiles({})
                setDoc(resp.data)
            } else {
                console.error(resp)
                event.target.disabled = false;
            }
        })
    }
    function removeItem(item){
        doc.items = doc.items.filter(i=>i!==item)
        setDoc({...doc})
    }
    
    return (<>
        <div>
            <h4>Define files to be uploaded <input type='file' multiple onChange={updateFiles}></input></h4>
            
            <div className={styles.filelist}>
                {Object.values(files).map((file)=><FileView key={file.name} remove={removeFile} file={file} stainSchema={stainSchema} blockSchema={blockSchema}></FileView>)}
            </div>
            <div>
                {Object.keys(files).length > 0 && <button onClick={saveFiles}>Save to the case</button>}
            </div>
            <h4>Current items</h4>
            <div className={styles.itemlist}>
                {items.map(item=><ItemView key={item._id} item={item} stainSchema={stainSchema} blockSchema={blockSchema} remove={removeItem}></ItemView>)}
            </div>
        </div>
    </>)
}

const CaseList = ()=>{
    const { data } = useLoaderData()
    console.log('loader data', data)

    return(<>
    <div>
        <h3>Create a new case</h3>
        <Link to={'create'}><button>New case</button></Link>
    </div>
    <div>
        <h3>Edit an existing case</h3>
        {data.map(c=>{
            return (<div key={c.bdsaCaseId} ><Link to={c.bdsaCaseId}>{c.bdsaCaseId}</Link></div>)
        })}
    </div>
    </>)
}

const CaseCreation = () => {
    const [schema, setSchema] = useState();
    const [saved, setSaved] = useState();
    const [index, setIndex] = useState(0);
    
    function onSave(doc){
        setSaved(doc)
    }

    return (
        <>
            <h3>Create a BDSA Case</h3>
            <SchemaSelector schemaName={'clinical'} onSelect={setSchema} immediate={true}></SchemaSelector>
            
            {schema && !saved && <CasePanel onSave={onSave} schema={schema}></CasePanel>}
            {saved && <div>
                <h4>Save was successful</h4>
                <Link to={`/manage/case/${saved.bdsaCaseId}`}><button>Continue to add slides</button></Link>
                or
                <button onClick={()=>{setSaved(null); setIndex(index+1); }}>Create another case</button>
            </div>}
        </>
    )
}

const CaseUpdate = ()=>{
    const { data, blockSchema, stainSchema } = useLoaderData()
    const [doc, setDocX] = useState(data)
    function setDoc(d){
        console.log('setDoc', d, d==doc)
        setDocX(d)
    }

    const [missing, setMissing] = useState(!doc);
    
    if(missing===true){
        return (<>
            <h3>Case not found</h3>
            <Link to={'/manage/case'}>View the list of cases</Link>
            </>)
    } else if(missing==='Case deleted'){
        return (<>
            <h3>Case deleted</h3>
            <Link to={'/manage/case'}>View the list of cases</Link>
            </>)
    } else {
        return (<>
            <h3>Case-level data for {data.bdsaCaseId}</h3>
            <CasePanel onDelete={()=>setMissing('Case deleted')} item={doc} ></CasePanel>
            <h3>Associated slides</h3>
            <SlidesPanel doc={doc} stainSchema={stainSchema} blockSchema={blockSchema} setDoc={setDoc}></SlidesPanel>
            </>)
    }
    
}


    /**
 * 
 * @returns Object the with fields "ok", "data" and "error" 
 */
function CaseLoader({params}){
    return api.get('bdsa/case',{query:{bdsaCaseId:params.bdsaCaseId}}).then(d => {
        if(d.status==200){
            
            return {
                ok: true,
                data: d.data
            }
        
        } else {
            return {
                ok: false,
                data: null,
                error: 'There was a problem contacting the DSA server.'
            }
        }
    }).then(resp=>{
        return api.get('bdsa/stain').then(d=>{
            if(d.status==200){
                resp.stainSchema = d.data;
            } else {
                resp.ok = false;
            }
            return resp;
        })
    }).then(resp=>{
        return api.get('bdsa/block').then(d=>{
            if(d.status==200){
                resp.blockSchema = d.data;
            } else {
                resp.ok = false;
            }
            return resp;
        });
    })
}
function CaseListLoader(){
    return api.get('bdsa/case').then(d => {
        console.log('case list loader response', d)
        if(d.status==200){
            
            return {
                ok: true,
                data: d.data
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


export default CaseCreation
export { CaseCreation, CaseUpdate, CaseLoader, CaseList, CaseListLoader }