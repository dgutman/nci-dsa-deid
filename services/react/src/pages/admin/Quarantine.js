import styles from './Quarantine.module.css';
import api from '../../API';
import formatBytes from '../../helpers/filesize';
// import { Fragment } from 'react';
import { useState, useCallback, memo } from 'react';
import {
    useQuery,
    // useMutation,
    // useQueryClient
  } from '@tanstack/react-query';

import FocusImage from '../../widgets/FocusImage';
import { JsonEditor } from 'json-edit-react';
import Validator  from 'jsonschema';
import Ajv from 'ajv';
import StainBlockSchemaPicker from '../../widgets/StainBlockSchemaPicker';
import { Link } from 'react-router-dom';

function QuarantineView(){
    
    const { isPending, isError, data: response, error } = useQuery({ queryKey: ['quarantine'], queryFn: () => api.get('bdsa/quarantine') });
    const { isPending: stainsPending, isError: stainsError, data: stainsResponse } = useQuery({ queryKey: ['stains'], queryFn: () => api.get('bdsa/stain').then(d=>d.status===200?d.data:[]) });
    const { isPending: blocksPending, isError: blocksError, data: blocksResponse } = useQuery({ queryKey: ['blocks'], queryFn: () => api.get('bdsa/block').then(d=>d.status===200?d.data:[]) });
    const AssociatedImage = ({id, image}) =>{
        const src = api.url(`item/${id}/tiles/images/${image}`);
        const [ enlargedImage, setEnlargedImage ] = useState(null);
        
        return (
            <>
                <div className={`${styles.image} ${styles['associated-image']}`}>
                    <label>{image}</label>
                    <img src={src} onClick={()=>setEnlargedImage(src)}></img>
                </div>
                {enlargedImage && <FocusImage src={enlargedImage} clearState={setEnlargedImage} style={{zIndex:1000}}></FocusImage>}
            </>
        )
    }
    const LargeImageItem = ({item, onClose}) => {
        console.log('LargeImageItem', item);
        const [isExpanded, setIsExpanded] = useState(false);
        const [enlargedImage, setEnlargedImage] = useState(null);
        const [metadata, setMetadata] = useState(item.meta);

        const { status:s, data: response1 } = useQuery({
            queryKey: [item._id],
            queryFn: () => api.get(`item/${item._id}/tiles/internal_metadata`),
            enabled: !!(item)
        });

        const { status:s2, data: response2 } = useQuery({
            queryKey: ['associated-images-'+item._id],
            queryFn: () => api.get(`item/${item._id}/tiles/images`).then(d=>{console.log('response2',d);return d;}),
            enabled: !!(item)
        });
        
        const thumbnailSrc = api.url(`item/${item._id}/tiles/thumbnail`)
        const [submissionState, setSubmissionState] = useState('Add to BDSA')
        const [deletionState, setDeletionState] = useState('Reject and delete')
        // console.log('stainsReponse', stainsResponse);

        function onStainChange(newStain){
            metadata.stain = newStain;
            setMetadata({...metadata});
        }
        function onBlockChange(newBlock){
            metadata.block = newBlock;
            setMetadata({...metadata});
        }
        return ( submissionState !== 'Closed' &&
            <>
                <div className={styles['quarantine-card']}>
                    <div className={styles['header']}>
                        <label>Name: </label><span>{item.name}</span>
                        <label>Size: </label><span>{formatBytes(item.size)}</span>
                        <label>DSA: </label><span><a href={`/dsa#item/${item._id}`}>Open</a></span>
                        <button onClick={()=>{
                                setSubmissionState('Pending...')
                                return api.post(`bdsa/quarantine/approve`, {query:{id:item._id}, body: {metadata}})
                                            .then(d=>{
                                                if(d.status==200){
                                                    setSubmissionState('Confirmed');
                                                } else {
                                                    setSubmissionState('Add to BDSA');
                                                }
                                            })
                                }
                            }
                            disabled={submissionState!=='Add to BDSA'||deletionState!=='Reject and delete'}
                            >
                            {submissionState}
                        </button>

                        <button onClick={()=>{
                                setDeletionState('Pending...')
                                return api.delete(`item/${item._id}`)
                                            .then(d=>{
                                                if(d.status==200){
                                                    setDeletionState('Deleted')
                                                } else {
                                                    setDeletionState('Reject and delete')
                                                }
                                            })
                                }
                            }
                            disabled={deletionState!=='Reject and delete' || submissionState!=='Add to BDSA'}
                            >
                            {deletionState}
                        </button>

                        {(submissionState=='Confirmed'||deletionState=='Deleted') && <button onClick={()=>{setSubmissionState('Closed'); onClose();}}>Close</button>}
                    </div>
                    <div>Thumbnail</div>
                    <div>Associated Images</div>
                    <div>Internal Metadata <span className={styles.expand} onClick={()=>setIsExpanded(!isExpanded)}>[{isExpanded?'-':'+'}]</span></div>
                    <div className={`${styles.thumbnail} ${styles['associated-image']}`} >
                        <img src={thumbnailSrc} style={{height:"100px", maxWidth:'100px'}} onClick={()=>setEnlargedImage(item._id)}/>
                    </div>
                    <div className={styles['associated-image']}>    
                        {s2 == 'success' && response2.data.map(image => <AssociatedImage key={item._id+image} id={item._id} image={image}></AssociatedImage>)}
                    </div>
                    <div className={`${styles['metadata']}} ${styles['internal-metadata']} ${isExpanded && styles.expanded}`}>
                        {s == 'success' && <pre>{JSON.stringify(response1.data, null, 2)}</pre>}
                    </div>
                    <div className={styles['metadata-opts']}>
                        <h4>Pick Schemas</h4>
                        <StainBlockSchemaPicker stainSchema={stainsResponse} 
                            blockSchema={blocksResponse} 
                            onStainChange={onStainChange} 
                            onBlockChange={onBlockChange}
                            stainVal = {item.meta.stain}
                            blockVal = {item.meta.block}></StainBlockSchemaPicker>
                    </div>
                    <div className={`${styles['item-metadata']}`}>
                        <h4>Slide Metadata</h4>
                        <JsonEditor data={metadata} setData={setMetadata} collapse={1}></JsonEditor>
                    </div>
                    {enlargedImage && <FocusImage wsi={enlargedImage} clearState={setEnlargedImage} style={{zIndex:1000}}></FocusImage>}
                    
                </div>
            </>
        )
    }

    const PlaceholderItem = ({item, onClose}) =>{
        
        return (
            <>
                <div className={styles['quarantine-card']}>
                    <div className={styles['header']}>
                        <label>Name: </label><span>{item.name}</span>
                        <label>Case: </label><span>{item.meta.bdsaCase}.  Modify/delete this item in the <Link to={`/manage/case/${item.meta.bdsaCase}`}>case editor page</Link>.</span>
                    </div>
                    
                    <div className={styles['metadata-opts']}>
                        <StainBlockSchemaPicker stainSchema={stainsResponse} 
                            blockSchema={blocksResponse} 
                            disabled={true}
                            stainVal = {item.meta.stain}
                            blockVal = {item.meta.block}></StainBlockSchemaPicker>
                    </div>
                    <div className={`${styles['item-metadata']}`}>
                        <JsonEditor data={item.meta} viewOnly={true} collapse={1}></JsonEditor>
                    </div>
                    
                    
                </div>
            </>
        )
    }

    const PendingCaseItem = ({item, onClose}) => {
        console.log('PendingCaseItem', item);
        const [isExpanded, setIsExpanded] = useState(false);
        const [enlargedImage, setEnlargedImage] = useState(null);

        const { status:s, data: response1 } = useQuery({
            queryKey: [item._id],
            queryFn: () => api.get(`item/${item._id}/tiles/internal_metadata`),
            enabled: !!(item)
        });

        const { status:s2, data: response2 } = useQuery({
            queryKey: ['associated-images-'+item._id],
            queryFn: () => api.get(`item/${item._id}/tiles/images`).then(d=>{console.log('response2',d);return d;}),
            enabled: !!(item)
        });
        
        const thumbnailSrc = api.url(`item/${item._id}/tiles/thumbnail`)
        const [deletionState, setDeletionState] = useState('Delete')
        

        return ( 
            <>
                <div className={styles['quarantine-card']}>
                    <div className={styles['header']}>
                        <label>Name: </label><span>{item.name}</span>
                        <label>Size: </label><span>{formatBytes(item.size)}</span>
                        <label>DSA: </label><span><a href={`/dsa#item/${item._id}`}>Open</a></span>

                        <button onClick={()=>{
                                setDeletionState('Pending...')
                                return api.delete(`item/${item._id}`)
                                            .then(d=>{
                                                if(d.status==200){
                                                    setDeletionState('Deleted')
                                                } else {
                                                    setDeletionState('Delete')
                                                }
                                            })
                                }
                            }
                            disabled={deletionState!=='Delete'}
                            >
                            {deletionState}
                        </button>

                        {(deletionState=='Deleted') && <button onClick={onClose}>Close</button>}
                    </div>
                    <div>Thumbnail</div>
                    <div>Associated Images</div>
                    <div>Internal Metadata <span className={styles.expand} onClick={()=>setIsExpanded(!isExpanded)}>[{isExpanded?'-':'+'}]</span></div>
                    <div className={`${styles.thumbnail} ${styles['associated-image']}`} >
                        <img src={thumbnailSrc} style={{height:"100px", maxWidth:'100px'}} onClick={()=>setEnlargedImage(item._id)}/>
                    </div>
                    <div className={styles['associated-image']}>    
                        {s2 == 'success' && response2.data.map(image => <AssociatedImage key={item._id+image} id={item._id} image={image}></AssociatedImage>)}
                    </div>
                    <div className={`${styles['metadata']}} ${styles['internal-metadata']} ${isExpanded && styles.expanded}`}>
                        {s == 'success' && <pre>{JSON.stringify(response1.data, null, 2)}</pre>}
                    </div>
                    
                    {enlargedImage && <FocusImage wsi={enlargedImage} clearState={setEnlargedImage} style={{zIndex:1000}}></FocusImage>}
                    
                </div>
            </>
        )
    }

    const Display = ({isPending, isError, response}) => {
        const [data, setData] = useState( response ? response.data : [])
        const [quarantined, setQuarantined] = useState(data.filter(item=>item.largeImage && item.meta.bdsaCase));
        const [pendingcase, setPendingCase] = useState(data.filter(item=>item.largeImage && !item.meta.bdsaCase));
        const pendingupload = data.filter(item=> !item.largeImage);

        if(isPending){
            return (
                <>
                    <div>Fetching...</div>
                </>
            )
        } else if (isError) {
            return (
                <>
                    <div>Oops, there was an error.</div>
                </>
            )
        } else if (response) {
            return (
                <>
                    <div className={styles['item-list']}>
                        <h2>Quarantined items awaiting review ({quarantined.length})</h2>
                        {quarantined.map((itemData) => (
                            <LargeImageItem key={itemData._id} item={itemData} onClose={()=>setQuarantined(quarantined.filter(i=>i != itemData))} />
                        ))}
                    </div>
                    <div className={styles['item-list']}>
                        <h2>Items awaiting image upload ({pendingupload.length})</h2>
                        {pendingupload.map((itemData) => (
                            <PlaceholderItem key={itemData._id} item={itemData} />
                        ))}
                    </div>
                    <div className={styles['item-list']}>
                        <h2>Uploads awaiting case creation ({pendingcase.length})</h2>
                        {pendingcase.map((itemData) => (
                            <PendingCaseItem key={itemData._id} item={itemData} onClose={()=>setPendingCase(pendingcase.filter(i=>i != itemData))} />
                        ))}
                    </div>
                </>
            )
        } else {
            return (
                <>
                <h2>What kind of state is this??</h2>
                </>
            )
        }
    }

    return (
        <>
        <h1>Quarantined Items</h1>
        <div>
           <Display isError={isError} isPending={isPending} response={response}></Display>
        </div>
        </>
    )
}

export default QuarantineView;