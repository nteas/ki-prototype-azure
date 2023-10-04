import React from 'react';
import ReactDOM from 'react-dom/client';
import { createHashRouter, RouterProvider } from 'react-router-dom';
import { initializeIcons } from '@fluentui/react';
import { MsalProvider } from '@azure/msal-react';
import {
	PublicClientApplication,
	EventType,
	AccountInfo,
} from '@azure/msal-browser';
import { msalConfig, useLogin } from './authConfig';

import './index.css';

import Layout from './pages/layout/Layout';
import Chat from './pages/chat/Chat';

initializeIcons();

const router = createHashRouter([
	{
		path: '/',
		element: <Layout />,
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
