import Home from './pages/Home';
import ErrorPage from './pages/ErrorPage';
import LoginPage from './pages/Login';
import AdminLayout from './layouts/Admin';
import ProtectedLayout from './layouts/Protected';
import BrowseLayout from './layouts/Browse';
import MyInfoPage from './pages/Me';
import APITest from './pages/apitest';
import AuthProvider from './providers/AuthContext';
import Base from './layouts/Base';

import AdminConfig , { Loader as AdminConfigLoader } from './pages/admin/Config';
import BrowseAll, { Loader as BrowseAllLoader } from './pages/browse/All';
import AdminNetwork from './pages/admin/Network';
import AdminTest from './pages/admin/Test';
import AdminQuarantine from './pages/admin/Quarantine';
import Upload from './pages/manage/upload';
import Basic, { Loader as ViewerLoader } from './pages/view/Basic';
import SchemaView, {Loader as SchemaLoader} from './pages/manage/SchemaView';
import Schemas from './pages/manage/Schemas';
import Stains, {Loader as StainLoader} from './pages/manage/Stains';
import Blocks, {Loader as BlockLoader} from './pages/manage/Blocks';
import {CaseCreation, CaseUpdate, CaseLoader, CaseList, CaseListLoader } from './pages/manage/Case';

import {
   createBrowserRouter,
   RouterProvider,
 } from "react-router-dom";
 
const App = () => {
   const router = createBrowserRouter([
      {
         element: <AuthProvider/>,
         children:[
            {
               path: "/",
               element: <Base />,
               children:[
                  {
                     errorElement: <ErrorPage/>,
                     children: [
                        {
                           // path: "/",
                           index:true,
                           element: <Home/>
                        },
                        {
                           path: "Login",
                           element: <LoginPage />,
                        },
                        {
                           path: "Me",
                           element: <MyInfoPage />,
                        },
                        {
                           path: "apitest",
                           element: <APITest />,
                        },
                        {
                           element: <AdminLayout/>,
                           children:[
                              {
                                 path: '/admin',
                              },
                              {
                                 path: '/admin/config',
                                 element: <AdminConfig/>,
                                 loader: AdminConfigLoader
                              },
                              {
                                 path: '/admin/network',
                                 element: <AdminNetwork/>,
                              },
                              {
                                 path: '/admin/test',
                                 element: <AdminTest/>
                              },
                              {
                                 path: '/admin/quarantine',
                                 element: <AdminQuarantine/>
                              },
                           ]
                        },
                        {
                           element: <ProtectedLayout/>,
                           children:[
                              {
                                 path: '/manage',
                              },
                              {
                                 path: '/manage/schema',
                                 element: <Schemas/>,
                              },
                              {
                                 path: '/manage/schema/:name',
                                 element: <SchemaView/>,
                                 loader: SchemaLoader
                              },
                              {
                                 path: '/manage/upload',
                                 element: <Upload/>,
                              },
                              {
                                 path: '/manage/case',
                                 element: <CaseList/>,
                                 loader: CaseListLoader,
                              },
                              {
                                 path: '/manage/case/create',
                                 element: <CaseCreation/>,
                              },
                              {
                                 path: '/manage/case/:bdsaCaseId',
                                 element: <CaseUpdate/>,
                                 loader: CaseLoader,
                              },
                              {
                                 path: '/manage/stains',
                                 element: <Stains/>,
                                 loader: StainLoader
                              },
                              {
                                 path: '/manage/blocks',
                                 element: <Blocks/>,
                                 loader: BlockLoader
                              }
                           ]
                        },
                        {
                           element: <BrowseLayout/>,
                           children:[
                              {
                                 path:'/browse'
                              },
                              {
                                 path:'/browse/all',
                                 element: <BrowseAll/>,
                                 loader: BrowseAllLoader
                              }
                           ]
                        },
                        {
                           path:'/view/basic/:id',
                           element: <Basic />,  
                           loader: ViewerLoader
                        },
                     ],
                  }
               ]
               
            },
            
         ]
      },
   ]);

    return <RouterProvider router={router} />

};
 
export default App;