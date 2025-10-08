import styles from './Base.module.css';
import LoginWidget from '../widgets/Login';
import { Outlet, NavLink } from 'react-router-dom';
import logo from '../assets/BDSA_clear.png';

function Base(){

    return(
        <>
        <div className={styles.fullpage}>
            <div className={styles.topbar}>
                <NavLink to="/"><img src={logo}/></NavLink>
                <span>
                    <NavLink to="/" className={styles.homelink}>Brain Digital Slide Archive</NavLink>
                </span>
                <LoginWidget></LoginWidget>
            </div>
            <div className={styles.app}>
                <Outlet />
            </div>
        </div>
        </>
    )
}

export default Base;

function Centered({ children }){
    return (
        <>
        <div className={styles.centeredWrapper}>
            <div className={styles.centered}>
                {children}
            </div>
        </div>
        </>
    )
}

function LeftNav({ children, navLinks }){
    const makeLink = (def, i) => {
        return (
            <NavLink key={i} to={def.to} className={styles.leftNavLink}>{def.text}</NavLink>
        )
    }
    return (
        <>
        <div className={styles.leftNavLayout}>
            <div className={styles.leftNav}>
                <ul>
                {navLinks.map(makeLink)}
                </ul>
            </div>
            <div className={styles.leftNavMain}>
                {children}
            </div>
        </div>
        </>
    )
}


export { Base, Centered, LeftNav };