import Spinner from 'react-bootstrap/Spinner';

export default function Component(): JSX.Element {
	return (
		<div
			style={{
				position: 'fixed',
				top: 0,
				left: 0,
				width: '100vw',
				height: '100vh',
				background: 'white',
				display: 'flex',
				alignItems: 'center',
				justifyContent: 'center',
				zIndex: 9999,
			}}>
			<Spinner animation="border" variant="primary">
				<span className="visually-hidden">Loading...</span>
			</Spinner>
		</div>
	);
}
