import api from '../../API';
import styles from './Schemas.module.css';
import { useLoaderData, useParams } from 'react-router-dom';
import { useState } from 'react';
import { JsonEditor } from 'json-edit-react';
import { Link } from 'react-router-dom';

function Schemas(){

    return (
        <>
        <h2>Select a schema to edit:</h2>
        <div className={styles.links}>
            <Link to={'slide'}><div>Slide</div></Link>
            <Link to={'clinical'}><div>Clinical</div></Link>
            <Link to={'region'}><div>Region</div></Link>
        </div>
        </>
    )
    
}


export default Schemas;