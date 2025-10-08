import { useAuth } from '../providers/AuthContext';


function Admin(){

    const { user } = useAuth();

    return (
        <>
        <div>
            <h3>Admin portal</h3>
            <pre>{window.JSON.stringify(user, null, 2)}</pre>
        </div>
        </>
    )
}

export default Admin;