
import { useLoaderData, useParams } from "react-router-dom";
import api from '../../API';
import BasicViewer from "../../widgets/BasicViewer";

function Basic(){
    const loaderData = useLoaderData()
    const { id } = useParams()
    console.log('loaderData', loaderData)
    console.log('id', id)
    return (<BasicViewer id={id} data={loaderData}></BasicViewer>)
}

function Loader({ params} ){
    return api.get(`item/${params.id}/tiles/`).then(d => {
        return d.data;
    });
}

export default Basic;
export { Loader }