import BasicViewer from "./BasicViewer"

const FocusImage = ({src, clearState, wsi, style}) => {
    if(!style) style = {}
    return (
        <>
            <div style={{position:'fixed',top:0, left: 0, width:'100vw', height:'100vh', display: src||wsi ? 'block' : 'none', ...style}}>
                <div style={{width:'100%', height:'100%', backgroundColor:'black', opacity:'70%'}} onClick={()=>clearState()}></div>
                <div style={{display:'inline-block', position:'fixed', top:'50%', left:'50%',transform:'translate(-50%, -50%'}}>
                    {
                    !wsi && <img src={src} style={{
                        maxWidth:'80vw',
                        maxHeight:'80vh',
                        objectFit:'contain',
                        width:'unset',
                        height:'unset',
                        }}></img>
                    }
                    {
                    wsi && <BasicViewer id={wsi} style={{
                        width:'80vw',
                        height:'80vh',
                        border:'thin black solid',
                        boxShadow:'black 5px 5px',
                        backgroundColor:'white'
                    }}></BasicViewer>
                    }
                    <span style={{
                        backgroundColor:'rgb(255, 115, 115)',
                        borderRadius:'0.5em',
                        position:'absolute',
                        top:'-2em', 
                        right:'-2em',
                        width:'1.4em',
                        height:'1.4em',
                        textAlign:'center',
                        border:'thin black solid',
                        cursor:'pointer'}} onClick={()=>clearState()}>X</span>
                </div>
                </div>
        </>
    )
}

export default FocusImage