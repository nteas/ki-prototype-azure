import React from 'react';
import ReactDOM from 'react-dom/client';
import { createHashRouter, Outlet, RouterProvider } from 'react-router-dom';
import { initializeIcons } from '@fluentui/react';

import './index.css';

import Layout from './components/Layout/Layout';
import Chat from './pages/chat/Chat';

initializeIcons();

const router = createHashRouter([
	{
		path: '/',
		element: <Outlet />,
		children: [
			{
				index: true,
				element: <Chat />,
			},
			{
				path: 'qa',
				lazy: () => import('./pages/oneshot/OneShot'),
			},
			{
				path: '*',
				lazy: () => import('./pages/NoPage'),
			},
		],
	},
]);

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
	<React.StrictMode>
		<RouterProvider router={router} />
	</React.StrictMode>
);
