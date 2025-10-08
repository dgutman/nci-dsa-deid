import styles from './Browse.module.css';
import { LeftNav } from '../layouts/Base';
import { Outlet } from 'react-router-dom';
function Browse(){

    // console.log(user);
    const navLinks = [
        {text:'Home', to:'/'},
        {text:'All WSIs', to:'/browse/all'},
    ]

    return (
        <>
        <LeftNav navLinks={navLinks}>
            <Outlet/>
        </LeftNav>
        </>
    )
}

export default Browse;