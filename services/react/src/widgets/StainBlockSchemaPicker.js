
import { useState } from 'react';

const StainBlockSchemaPicker = ({stainVal, blockVal, stainSchema, blockSchema, onStainChange, onBlockChange,disabled}) => {
    blockSchema = blockSchema || [];
    stainSchema = stainSchema || [];

    const [stain, setStain] = useState(stainVal);
    const [block, setBlock] = useState(blockVal);

    function stainSchemaSelected(ev){
        const index = ev.target.value;
        const newStain = stainSchema[index]
        setStain(newStain)
        onStainChange(newStain)
    }
    function blockSchemaSelected(ev){
        const index = ev.target.value;
        const newBlock = blockSchema[index]
        setBlock(newBlock)
        onBlockChange(newBlock)
    }
    
    const blockIndex = blockSchema.findIndex(s=>s._id==block?._id)
    const stainIndex = stainSchema.findIndex(s=>s._id==stain?._id)
    
    return (<>
        <div>
            <label>Block: </label>
            <select onChange={blockSchemaSelected} value={blockIndex} disabled={disabled}>
                <option disabled value={-1}> -- select an option -- </option>
                {blockSchema.map((item,idx)=> <option key={item._id} value={idx}>{item.name}</option>)}
            </select>
        </div>
        <div>
            <label>Stain: </label>
            <select onChange={stainSchemaSelected} value={stainIndex} disabled={disabled}>
                <option disabled value={-1}> -- select an option -- </option>
                {stainSchema.map((item,idx)=> <option key={item._id} value={idx}>{item.name}</option>)}
            </select>
        </div>
    </>)
}

export default StainBlockSchemaPicker;