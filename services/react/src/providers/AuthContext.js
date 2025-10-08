import { useContext, createContext, useState, useEffect } from "react";
import { useOutlet } from "react-router-dom";

import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'


import api from '../API.js';



const AuthContext = createContext();
const queryClient = new QueryClient();

const AuthProvider = () => {
  const outlet = useOutlet();

  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.girderToken);

  // The first time we mount, get our current status
  useEffect(()=>{
      api.get('user/me').then(d=>setUser(d.data));
  }, []);

  // Any time localStorage changes, get our current status
  useEffect(() => {
  
      const onStorageChange = ()=>{
        // Local storage may have changed, but if the girderToken is the same as our existing one, don't refresh
        if(localStorage.girderToken === token){
          return;
        }
        // Ok, new girderToken, get our new user info
        api.get('user/me').then(d=>{
          setUser(d.data);
        });
      }
      window.addEventListener('storage', onStorageChange);
      
      return ()=> window.removeEventListener('storage', onStorageChange);
          
  }, [])


  /**
   * onLoginResponse
   * @param {Response} resp 
   * @returns status: true if login succeeded, false otherwise.
   */
  const onLoginResponse = (resp) => {
    if(resp.data && resp.data.authToken){
      localStorage.setItem('girderToken', resp.data.authToken.token);
      setToken(resp.data.authToken.token);
      setUser(resp.data.user);
      return true;
    } else {
      setUser(null);
      setToken(null);
      localStorage.setItem('girderToken', null);
      return false;
    }
  }
  const onLogoutResponse = () => {
    setUser(null);
    setToken(null);
    localStorage.setItem('girderToken', null);
  }




  const doLogin = async (username, password)=>{
    const headers = {
      Authorization: `Basic ${btoa(username + ":" + password)}`,
    }
    return api.get('/user/authentication', {headers}).then(onLoginResponse);
  }
  const doLogout = async ()=>{
    return api.delete('/user/authentication').then(onLogoutResponse);
  }

  return (
    <>
      <QueryClientProvider client={queryClient}>
        <AuthContext.Provider value={{user, doLogin, doLogout}}>{outlet}</AuthContext.Provider>
      </QueryClientProvider>
    </>
  
  );
};

export default AuthProvider;

export const useAuth = () => {
  return useContext(AuthContext);
};
