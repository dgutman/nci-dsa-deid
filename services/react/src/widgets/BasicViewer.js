import styles from './BasicViewer.module.css'
import { useEffect, useState } from 'react';
import OpenSeadragon from 'openseadragon';
import api from '../API';
// import { useAuth } from '../../providers/AuthContext';

class CustomTileSource extends OpenSeadragon.TileSource {
    constructor(baseUrl, metadata) {
        super({
            width: metadata.sizeX,
            height: metadata.sizeY,
            tileWidth: metadata.tileWidth,
            tileHeight: metadata.tileHeight,
            minLevel: 0,
            maxLevel: metadata.levels-1
        });
        this.baseUrl = baseUrl;
    }

    getTileUrl(level, x, y) {
        return `${this.baseUrl}/${level}/${x}/${y}`;
    }

    getTileAjaxHeaders() {
        return {
            'Girder-Token': localStorage.girderToken
        };
    }
}

/**
 * 
 * @param {string} id the girderID of the item
 * @param {object} data 
 * @returns 
 */
function BasicViewer({id, data, style}){
    console.log('bv id', id)
    console.log('bv data', data)

    const [tileData, setTileData] = useState(data)

    useEffect(() => {
        if(!tileData){
            api.get(`item/${id}/tiles`).then(d=>{
                setTileData(d.data)
            })
        } 

        let source = tileData && new CustomTileSource(api.url(`item/${id}/tiles/zxy`), tileData);
        
        let viewer = OpenSeadragon({
            id: 'seadragon-viewer-'+id,
            prefixUrl: '//openseadragon.github.io/openseadragon/images/',
            tileSources: tileData ? source : []
        });
    
        // Cleanup (equal to componentWillUnmount)
        return () => {
            viewer.destroy();
            viewer = null;
        };
    }, [tileData]);
    
    return (
        <div id={"seadragon-viewer-"+id} className={styles.viewer} style={style}/>
    );
    
}

export default BasicViewer;
