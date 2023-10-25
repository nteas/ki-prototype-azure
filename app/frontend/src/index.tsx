import React from 'react';
import ReactDOM from 'react-dom/client';
import { createBrowserRouter, Outlet, RouterProvider } from 'react-router-dom';
import { initializeIcons } from '@fluentui/react';

// import { MsalProvider } from '@azure/msal-react';
// import {
// 	PublicClientApplication,
// 	EventType,
// 	AccountInfo,
// } from '@azure/msal-browser';

// import { msalConfig } from './authConfig';
import Chat from './pages/chat/Chat';
import 'bootstrap/dist/css/bootstrap.min.css';

import './index.css';

// const msalInstance = new PublicClientApplication(msalConfig);

// if (
// 	!msalInstance.getActiveAccount() &&
// 	msalInstance.getAllAccounts().length > 0
// ) {
// 	msalInstance.setActiveAccount(msalInstance.getActiveAccount());
// }

// msalInstance.addEventCallback(event => {
// 	console.log(event.payload);
// 	if (event.eventType === EventType.LOGIN_SUCCESS && event.payload) {
// 		const account = event.payload as AccountInfo;
// 		msalInstance.setActiveAccount(account);
// 	}
// });

initializeIcons();

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
				path: 'qa',
				lazy: () => import('./pages/oneshot/OneShot'),
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
	<React.StrictMode>
		<RouterProvider router={router} />
	</React.StrictMode>
);
