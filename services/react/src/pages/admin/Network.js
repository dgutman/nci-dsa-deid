import api from '../../API';
import styles from './Network.module.css';
import { Link } from 'react-router-dom';
import { useState } from 'react';
import {
    useQuery,
    useMutation,
    useQueryClient
  } from '@tanstack/react-query';

function Network(){
    // use the query client to sync with server side data
    const queryClient = useQueryClient();

    const refreshConnections = useMutation({
        mutationFn: () => true,
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['network-config'] }), // Invalidate and refetch
    })

    const deleteConnection = useMutation({
        mutationFn: id => api.delete('bdsa/network/connection', {query:{id}}),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['network-config'] }), // Invalidate and refetch
    })

    const cancelConnection = useMutation({
        mutationFn: id => api.put('bdsa/network/connection', {query:{id, action:'cancel'}}),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['network-config'] }), // Invalidate and refetch
    })

    const rejectConnection = useMutation({
        mutationFn: id => api.put('bdsa/network/connection', {query:{id, action:'reject'}}),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['network-config'] }), // Invalidate and refetch
    })

    const approveConnection = useMutation({
        mutationFn: id => api.put('bdsa/network/connection', {query:{id, action:'approve'}}),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['network-config'] }), // Invalidate and refetch
    })

    const deleteRemoteBdsa = useMutation({
        mutationFn: id => api.delete('bdsa/network/remote', {query:{id}}),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['network-config'] }), // Invalidate and refetch
    })

    const toggleRemoteBdsa = useMutation({
        mutationFn: ({id, disableApiKey}) => api.put('bdsa/network/activate', {query:{id, disableApiKey}}),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['network-config'] }), // Invalidate and refetch
    })

    const syncRemote = useMutation({
        mutationFn: ({assetstoreId, folderId}) => {
                console.log('syncRemote', assetstoreId, folderId)
                return api.put('bdsa/network/sync', {query:{assetstoreId, folderId}})
            },
        // onSuccess: () => queryClient.invalidateQueries({ queryKey: ['network-config'] }), // Invalidate and refetch
    })

    const { isPending, isError, data, error } = useQuery({ queryKey: ['network-config'], queryFn: () => api.get('bdsa/network/describe') });

    // const bdsas = data?.data.info.filter(bdsa => bdsa.role === 'remote') || [];
    console.log('data',data)
    const local = data?.data?.info?.filter(bdsa => bdsa.role === 'local')[0];
    const remotes = data?.data?.info?.filter(bdsa => bdsa.role === 'remote') || [];
    const connections = data?.data?.connections || [];
    const pending = connections.filter(c=>['initiated', 'unverified', 'awaiting-approval', 'connecting'].includes(c.status))
    const connected = connections.filter(c=>['connected'].includes(c.status))
    const canceled = connections.filter(c=>['canceled', 'rejected'].includes(c.status))



    // Stateful variables
    const [bdsaUrl, setBdsaUrl] = useState('');
    const updateUrl = (event) => setBdsaUrl(event.target.value);
    const [connectionMsg, setConnectionMsg] = useState('');

    // Initiate connection
    const initiateConnection = (event)=>{
        console.log('Initiating connection to', bdsaUrl);
        api.post('bdsa/network/connection', {query: {url: bdsaUrl}}).then(d=>{
            setConnectionMsg(d.data?.message || d.data?.error);
            console.log(d)
            queryClient.invalidateQueries({ queryKey: ['network-config'] }); // refresh the list of connections
        });
    }

    const RemoteBdsa = (info) => {
        return (
            <li key={info.uuid}>
                <div className={styles.bdsaInfo}>
                    <div className={styles.remoteBdsaHeader}>
                        <Link to={`/dsa/#folder/${info.folder?._id}`}>
                            <span className={styles.name}>{info.remoteDetails.displayName}</span>
                            <button>View</button>
                        </Link>
                        <span className={styles.syncContainer}>
                            <button className={styles.syncButton} onClick={()=>
                                {
                                    console.log('calling syncRemote', info.assetstore._id, info.folder?._id)
                                    syncRemote.mutate({assetstoreId: info.assetstore._id, folderId: info?.folder._id})
                                }}
                                >Sync data from remote BDSA</button>
                        </span>
                        <button className={styles.pauseButton} data-paused={info.paused} onClick={()=>toggleRemoteBdsa.mutate(info._id, !info.paused)}>{info.paused ? 'Resume access' : 'Pause access'}</button>
                        <button className={styles.deleteButton} onClick={()=>deleteRemoteBdsa.mutate(info._id)}>Permanently Delete</button>
                        <span>
                            <label>Contact:</label><span>{info.remoteDetails.contactName}</span>
                            <label>Email:</label><span>{info.remoteDetails.contactEmail}</span>
                        </span>
                    </div>
                    
                    {/* <pre>{JSON.stringify(info, null, 2)}</pre> */}
                </div>
            </li>
        )
    }

    const BdsaConnection = (conn) =>{
        // const [expanded, setExpanded ] = useState(false);
        console.log('Making bdsa connection widget', conn)

        function ActionButtons(id, status){
            if(status==='initiated' || status==='connected'){
                return (
                    <>
                        <button onClick={()=>cancelConnection.mutate(id)}>Cancel</button>
                    </>
                )
            } else if (status === 'unverified' || status === 'awaiting-approval') {
                return (
                    <>
                        <button onClick={()=>approveConnection.mutate(id)}>Approve</button>
                        <button onClick={()=>rejectConnection.mutate(id)}>Reject</button>
                    </>
                )
            } else if (status === 'canceled' || status === 'rejected') {
                return (
                    <>
                        <button onClick={()=>deleteConnection.mutate(id)}>Delete</button>
                    </>
                )
            }
        }

        function Info(conn){
            const status = conn.status;
            if (status === 'unverified' || status === 'awaiting-approval') {
                const emailVerified = status === 'unverified' ? 'verified' : "unverified";
                return (
                    <>
                        <div><label>Url:</label> {conn.url}</div>
                        <div><label>Initiated by:</label> {conn.contactName}</div>
                        <div><label>Email: </label> <span className={styles[emailVerified]}>{conn.contactEmail}</span></div>
                    </>
                )
            } else {
                return (
                    <>
                    <label>URL:</label><div>{conn.url}</div>
                    </>
                )
            }
        }
        return (
            <div key={conn.uuid} className={styles.connection} data-uuid={conn.uuid}>
                <div><label>Status:</label><div>{conn.status}</div></div>
                <div>{Info(conn)}</div>
                <div>
                    {ActionButtons(conn._id, conn.status)}
                </div>
            </div>
        )
    }

    if(!local){
        return (
            <>
            <h3>You must <Link to="/admin/config">configure this BDSA</Link> before connecting to the network.</h3>
            </>
        )
    }


    return (
        <>
        <div className={styles.page}>
            <h1>BDSA Network Setup</h1>
            <div className={styles.section}>
                <h3>Request connection to a new BSDA instance</h3>
                <label>Web address: <input type='text' placeholder='Enter the URL of a BDSA site' value={bdsaUrl} onChange={updateUrl}/></label> <button onClick={initiateConnection}>Send request</button>
                <div>{connectionMsg}</div>
            </div>

            <div className={styles.section}>
                <h3>All connections</h3>
                <button onClick={refreshConnections.mutate}>Refresh</button>
                
                <div className={styles.connectionList}>
                    <h3>Pending ({pending.length})</h3>
                    <div className={styles.connections}>{pending.map(BdsaConnection)}</div>
                </div>

                <div className={styles.connectionList}>
                    <h3>Connected ({connected.length})</h3>
                    <div className={styles.connections}>{connected.map(BdsaConnection)}</div>
                </div>

                <div className={styles.connectionList}>
                    <h3>Canceled & Rejected ({canceled.length})</h3>
                    <div className={styles.connections}>{canceled.map(BdsaConnection)}</div>
                </div>
            </div>
            
            <div className={styles.section}>
                <h3>Remote BSDAs</h3>
                {remotes.map(remote=>RemoteBdsa(remote))}
            </div>

        </div>
        </>
    )
}

// function Loader(){
//     return api.get('bdsa/network');
// }

export default Network;
// export { Loader };