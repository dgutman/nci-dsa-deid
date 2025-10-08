import { useRouteError, isRouteErrorResponse } from 'react-router-dom';
import styles from './ErrorPage.module.css';

function ErrorPage() {
    let error = useRouteError();
    let errorMessage;

    if (isRouteErrorResponse(error)) {
        // error is type `ErrorResponse`
        console.log('Route response error', error);
        errorMessage = error.error?.message || error.statusText;
    } else if (error instanceof Error) {
        console.log('Error error', JSON.stringify(error, null, 2));
        errorMessage = error.error?.message;
    } else if (typeof error === 'string') {

        console.log('string error', error);
        errorMessage = error;
    } else {

        console.log('Other error', error);
        console.error(error);
        errorMessage = 'Unknown error';
    }

    return (
    <>
    <div className={styles.root}>
        <h2>Oops, looks like something went wrong.</h2>
        <p>{errorMessage}</p>
        {/* <pre>{JSON.stringify(error, null, 2)}</pre> */}
        {/* <pre className={styles.stack}>{error.error.stack}</pre> */}
    </div>
    </>
    );
 }

 export default ErrorPage;