// import logo from './logo.svg';
import logo from '../assets/BDSA_clear.png';
import styles from './Home.module.css';
import { Centered } from '../layouts/Base';
import { Link } from 'react-router-dom';

function Home() {
  return (
    <Centered>
      <div className={styles.Home}>
        
          <h1>Welcome to the BDSA <img src={logo} className={styles["App-logo"]} alt="logo" /></h1>
          <h3>View BDSA Slides</h3>
          <ul>
            <Link to='/browse/all'>See all slides</Link>
          </ul>
          <h3>Administrators: Configure the BDSA</h3>
          <ul>
            <Link to='/admin'>Admin homepage (login required)</Link>
          </ul>
          <h3>Services</h3>
          <ul>
            <li><a href='/dsa'>Access the Digital Slide Archive (Girder) service</a></li>
            <li><a href='/dsa/api/v1'>Access the Girder REST API</a></li>
            <li><a href='/mongodb'>Access the read-only mongo-express service</a></li>
          </ul>
          <h3>Development</h3>
          <p>
            Edit files in <code>/services/react</code> and save to reload.
          </p>
      
      </div>
    </Centered>
  );
}

export default Home;
