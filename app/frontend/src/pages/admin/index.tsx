import Layout from '../../components/Layout/Layout';

export function Component(): JSX.Element {
	return (
		<Layout logoSuffix="ADMIN">
			<h1>Admin Page</h1>
		</Layout>
	);
}

Component.displayName = 'AdminPage';
