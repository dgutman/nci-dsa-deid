import styles from './Login.module.css';
import { useState, useEffect, useRef } from 'react';
import api from '../API.js';
import { useAuth } from '../providers/AuthContext';

function AccountInfo(setExpanded){

    const { user, doLogin, doLogout } = useAuth();

    const [ disabled, setDisabled ] = useState(false);
    const [ status, setStatus ] = useState(false);

    const onSubmit = (event) => {
        event.preventDefault();
        const data = Object.fromEntries(new FormData(event.target));
        doLogin(data.username, data.password).then((success)=>{
            setStatus(success)
            setDisabled(false)
            if(success){
                setExpanded(false);
            }
        });
        setStatus(false);
        setDisabled(true);
        return false;
    }

    const loginResponse = (success) => {
        if(success){
            return <></>
        } else {
            return <span className={styles.loginFailed}>Incorrect username/password</span>
        }
    }
    const loggedOut = (
        <>
        <div className = {styles.background}></div>
        <div className = {styles.loginDialog}>
            <h3>Enter your login information</h3>
            <form onSubmit={onSubmit}>
                <div className={styles.loginInputs}>
                    <label htmlFor="username">Username: </label><input type="text" name="username" placeholder='Username' required></input>
                    <label htmlFor="password">Password: </label><input type="password" name="password" placeholder='Password' required></input>
                </div>
                <div className={styles.failedLogin}>{loginResponse(status)}</div>
                <input type="submit"  disabled={disabled && "disabled"}></input>
            </form>
            
            <a href={`/dsa#?dialog=register`}>Create account</a> | <a href={`dsa#?dialog=resetpassword`}>Forgot password?</a>
        </div>
        </>
    )

    const loggedIn = (
        <>
        <div className={styles.logoutDialog}>
            <button onClick={()=>doLogout()}>Log out</button>
            <br></br>
            <a href={`/dsa/#useraccount/${user && user._id}/info`}>View my account</a>
            <hr></hr>
            <button onClick={()=>api.put('system/restart')}>Restart the DSA</button>
        </div>
        </>
    )

    return (<>
        {user && user._id ? loggedIn : loggedOut}    
    </>)
}

function Expanded(expanded, setExpanded){
    useEffect(() => {
        function cancelDialog(){
            setExpanded(false);
        }

        window.addEventListener('click', cancelDialog);
        
        return () => {
          window.removeEventListener('click', cancelDialog);
        }
    }, []);

    const dropdownClick = (event)=>event.stopPropagation();

    const dropdown = (<>
        <div className = {styles.dropdown} onClick={dropdownClick}>
            {AccountInfo(setExpanded)}
        </div>
    </>)

    return expanded ? dropdown : null;
}

function LoginWidget(){
    const [ expanded, setExpanded ] = useState(false);

    const { user } = useAuth();

    const buttonClasses = [styles.loginbutton, expanded && styles.expanded, user && user._id && styles.loggedIn].join(' ');

    const buttonClick = (event)=>{
        event.stopPropagation();
        setExpanded(!expanded);
    }
    return (
        <div className={styles.widget}>
            <span className={buttonClasses} onClick={buttonClick}>
                <span className={styles.username}>{user && user.login}</span>
                <span className={styles.expand}></span>
            </span>
            {Expanded(expanded, setExpanded)}
            
        </div>
      );
}

export default LoginWidget;