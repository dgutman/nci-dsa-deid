import styles from './WsiCard.module.css';
import api from '../API';
import { Link } from 'react-router-dom';

function WsiCard(item){
    console.log('making wsi card', item._id)
    return (
        <div key={item._id} className={styles.wsiCard}>
            <Link to={`/view/basic/${item._id}`}>
                <div>
                    <img src={api.url(`/item/${item._id}/tiles/thumbnail?encoding=JPEG`)}></img>
                </div>
            </Link>
        </div>
    )
}

export default WsiCard;