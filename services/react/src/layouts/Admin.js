import { useAuth } from '../providers/AuthContext';
import styles from './Admin.module.css';
import { LeftNav } from '../layouts/Base';
import { Outlet } from 'react-router-dom';
function Admin(){

    const { user } = useAuth();

    // throw new Error('Test Error')
    if(!user || !user.admin){
        return (<>
        <div><h2>Please log in as an administrator to view this page</h2></div>
        </>);
    }

    // console.log(user);
    const navLinks = [
        {text:'Home', to:'/'},
        {text:'Configure BDSA', to:'/admin/config'},
        {text:'Link to other BDSAs', to:'/admin/network'},
        {text:'Quarantined items', to:'/admin/quarantine'},
        {text:'Test', to:'/admin/test'},
        {text:'Management portal', to:'/manage'},
    ]

    return (
        <>
        <LeftNav navLinks={navLinks}>
            <Outlet/>
        </LeftNav>
        </>
    )
}

export default Admin;