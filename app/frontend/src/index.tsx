import ReactDOM from 'react-dom/client';
import { createBrowserRouter, Outlet, RouterProvider } from 'react-router-dom';

import Chat from './pages/chat/Chat';
import 'bootstrap/dist/css/bootstrap.min.css';
import './index.scss';

const router = createBrowserRouter([
	{
		path: '/',
		element: <Outlet />,
		children: [
			{
				index: true,
				element: <Chat />,
			},
			{
				path: 'logs',
				lazy: () => import('./pages/logs/Logs'),
			},
			{
				path: 'admin',
				children: [
					{
						index: true,
						lazy: () => import('./pages/admin'),
					},
					{
						path: 'create',
						lazy: () => import('./pages/admin/CreateSource'),
					},
					{
						path: 'edit/:id',
						lazy: () => import('./pages/admin/EditSource'),
					},
					// {
					// 	path: 'delete',
					// 	lazy: () => import('./pages/admin/DeleteSource'),
					// },
				],
			},
			{
				path: '*',
				lazy: () => import('./pages/NoPage'),
			},
		],
	},
]);

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
	<RouterProvider router={router} />
);
