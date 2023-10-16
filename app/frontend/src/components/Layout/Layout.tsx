import { NavLink, Link, useNavigate } from 'react-router-dom';

import styles from './Layout.module.css';

interface Props {
	headerActions?: React.ReactNode;
	children: React.ReactNode;
}

const Layout = ({ headerActions, children }: Props) => {
	const navigate = useNavigate();
	return (
		<div className={styles.layout}>
			<header className={styles.header} role="banner">
				<div className={styles.headerContainer}>
					<Link to="/" className={styles.headerTitleContainer}>
						<img
							src="data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz4KPCEtLSBHZW5lcmF0b3I6IEFkb2JlIElsbHVzdHJhdG9yIDIzLjAuMCwgU1ZHIEV4cG9ydCBQbHVnLUluIC4gU1ZHIFZlcnNpb246IDYuMDAgQnVpbGQgMCkgIC0tPgo8c3ZnIHZlcnNpb249IjEuMSIgaWQ9IkxheWVyXzEiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgeG1sbnM6eGxpbms9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkveGxpbmsiIHg9IjBweCIgeT0iMHB4IgoJIHZpZXdCb3g9IjAgMCAxNjcgODAiIHN0eWxlPSJlbmFibGUtYmFja2dyb3VuZDpuZXcgMCAwIDE2NyA4MDsiIHhtbDpzcGFjZT0icHJlc2VydmUiPgo8c3R5bGUgdHlwZT0idGV4dC9jc3MiPgoJLnN0MHtmaWxsOiNGRkZGRkY7fQoJLnN0MXtmaWxsOiM3QkMyRTM7fQoJLnN0MntvcGFjaXR5OjAuMzg7fQoJLnN0M3tmaWxsOnVybCgjU1ZHSURfMV8pO30KCS5zdDR7ZmlsbDp1cmwoI1NWR0lEXzJfKTt9Cgkuc3Q1e2ZpbGw6IzZDQkZFMjt9Cgkuc3Q2e2ZpbGw6IzQxQjRERTt9Cgkuc3Q3e2ZpbGw6IzAwQUFENDt9Cgkuc3Q4e2ZpbGw6IzAwOUZEMzt9Cgkuc3Q5e2ZpbGw6IzAwOTdDRjt9Cjwvc3R5bGU+CjxwYXRoIGNsYXNzPSJzdDAiIGQ9Ik03NS4zLDI2LjRjMCwwLDYuNi0xMiw4LjYtMTUuMWMyLTMuMSw3LjQtOS43LDEzLjItOS43YzUuOC0wLjEsOS4zLDMuMiwxMS45LDYuNWMyLjYsMy4yLDgsMTIuOCw5LjcsMTUuMwoJYzEuNywyLjUsNSw3LDguNiw5LjJjMy42LDIuMiw1LjQsMi4yLDUuNCwyLjJzLTYuNCwwLTEwLjEsMHMtMTAuOC0xLjEtMTQuNS0zLjJzLTcuNi01LjItMTIuMS03LjljLTQuNS0yLjctNy44LTIuOS0xMC4zLTIuNwoJYy0yLjUsMC4yLTUuOCwxLjctNy4zLDIuOVM3NS4zLDI2LjQsNzUuMywyNi40eiIvPgo8Zz4KCTxwYXRoIGNsYXNzPSJzdDEiIGQ9Ik03Ni41LDI1LjRjLTkuMyw3LjUtMTcuNiwyMi0zMCwyMkMyOS4yLDQ3LjQsMjkuOSwzNSw4LjIsMzVINy4xYzIyLjQsMCwyMC40LDMwLDQxLjUsMzAKCQlDNjAuOCw2NSw2OC4zLDQzLjUsNzYuNSwyNS40TDc2LjUsMjUuNHoiLz4KCTxnIGNsYXNzPSJzdDIiPgoJCQoJCQk8bGluZWFyR3JhZGllbnQgaWQ9IlNWR0lEXzFfIiBncmFkaWVudFVuaXRzPSJ1c2VyU3BhY2VPblVzZSIgeDE9Ii0xMjMuMTIxMyIgeTE9IjMzMi43OTIyIiB4Mj0iLTExOS42NDQzIiB5Mj0iMzMyLjc5MjIiIGdyYWRpZW50VHJhbnNmb3JtPSJtYXRyaXgoLTIuMjkxOSAwLjQxNzggNi44NTAwMDBlLTAyIDAuMzc1NyAtMjQ4LjU4ODcgLTE4Ljk2NjEpIj4KCQkJPHN0b3AgIG9mZnNldD0iMCIgc3R5bGU9InN0b3AtY29sb3I6I0ZGRkZGRjtzdG9wLW9wYWNpdHk6MCIvPgoJCQk8c3RvcCAgb2Zmc2V0PSIxIiBzdHlsZT0ic3RvcC1jb2xvcjojRkZGRkZGIi8+CgkJPC9saW5lYXJHcmFkaWVudD4KCQk8cG9seWdvbiBjbGFzcz0ic3QzIiBwb2ludHM9IjUwLjcsNjUuMSA1NC40LDYzLjkgNTcuNiw2MS4xIDU0LjcsNDUuNSA0Ni45LDQ3LjUgCQkiLz4KCQkKCQkJPGxpbmVhckdyYWRpZW50IGlkPSJTVkdJRF8yXyIgZ3JhZGllbnRVbml0cz0idXNlclNwYWNlT25Vc2UiIHgxPSItNzEuNDAyNiIgeTE9IjMzMi44MzUiIHgyPSItNjcuNzUzNiIgeTI9IjMzMi44MzUiIGdyYWRpZW50VHJhbnNmb3JtPSJtYXRyaXgoMi4yOTE5IC0wLjQxNzggNi44NTAwMDBlLTAyIDAuMzc1NyAxODEuNDY5MSAtOTguMDY0NykiPgoJCQk8c3RvcCAgb2Zmc2V0PSIwIiBzdHlsZT0ic3RvcC1jb2xvcjojRkZGRkZGO3N0b3Atb3BhY2l0eTowIi8+CgkJCTxzdG9wICBvZmZzZXQ9IjEiIHN0eWxlPSJzdG9wLWNvbG9yOiNGRkZGRkYiLz4KCQk8L2xpbmVhckdyYWRpZW50PgoJCTxwb2x5Z29uIGNsYXNzPSJzdDQiIHBvaW50cz0iNTAuOCw2NS4xIDQ2LjcsNjUuMSA0Mi44LDY0LjEgMzguOCw0NyA0Ni44LDQ3LjMgCQkiLz4KCTwvZz4KPC9nPgo8Zz4KCTxwYXRoIGNsYXNzPSJzdDUiIGQ9Ik00OC42LDY1LjZDMzgsNjUuNiwzMyw1OCwyOC4yLDUwLjdjLTQuOS03LjQtMTAtMTUuMS0yMS4xLTE1LjFIMi45di0wLjloNC4yYzExLjYsMCwxNi44LDcuOSwyMS44LDE1LjUKCQljNC45LDcuNCw5LjUsMTQuNSwxOS42LDE0LjVjMTAuMiwwLDE3LjMtMTYuMSwyNC4xLTMxLjZDNzkuNiwxNy4zLDg2LjgsMSw5Ny42LDFjOC4zLDAsMTIuOSw3LjcsMTcuOCwxNS45CgkJYzUuMiw4LjcsMTAuNSwxNy44LDIwLjksMTcuOGgyNi45djAuOWgtMjYuOWMtMTAuOSwwLTE2LjQtOS4zLTIxLjctMTguMmMtNC43LTgtOS4yLTE1LjUtMTctMTUuNWMtMTAuMiwwLTE3LjMsMTYuMS0yNC4xLDMxLjYKCQlDNjYuNiw0OS4yLDU5LjQsNjUuNiw0OC42LDY1LjZMNDguNiw2NS42eiIvPgoJPHBhdGggY2xhc3M9InN0NiIgZD0iTTQ4LjEsNjEuM2MtMTAuMSwwLTE0LjktNi40LTE5LjYtMTIuNWMtNC45LTYuNC05LjktMTMuMS0yMS4xLTEzLjFIMi45di0xLjFoNC41YzExLjcsMCwxNi45LDYuOSwyMS45LDEzLjUKCQljNC43LDYuMiw5LjIsMTIuMSwxOC44LDEyLjFjOS43LDAsMTYuNi0xMy44LDIzLjMtMjcuMkM3OC4xLDE5LjYsODUsNS44LDk0LjksNS44YzcuOSwwLDEyLjMsNi40LDE3LDEzLjIKCQljNS4zLDcuNiwxMC43LDE1LjUsMjEuNiwxNS41aDI5Ljd2MS4xaC0yOS43Yy0xMS41LDAtMTcuMy04LjUtMjIuNS0xNmMtNC41LTYuNi04LjgtMTIuOC0xNi4xLTEyLjhjLTkuMywwLTE2LDEzLjUtMjIuNSwyNi42CgkJQzY1LjUsNDcuMSw1OC41LDYxLjMsNDguMSw2MS4zTDQ4LjEsNjEuM3oiLz4KCTxwYXRoIGNsYXNzPSJzdDciIGQ9Ik00Ny42LDU3Yy05LjUsMC0xNC4zLTUuMi0xOC45LTEwLjNjLTQuOS01LjQtOS45LTExLTIxLjEtMTFIMi45di0xLjNoNC44YzExLjcsMCwxNi45LDUuOCwyMiwxMS40CgkJYzQuNiw1LjEsOC45LDkuOCwxNy45LDkuOGM5LjIsMCwxNi0xMS42LDIyLjYtMjIuOGM2LjctMTEuNCwxMy0yMi4zLDIyLjEtMjIuM2M3LjUsMCwxMS44LDUuMiwxNi4zLDEwLjcKCQljNS4zLDYuNSwxMC44LDEzLjEsMjIuMywxMy4xaDMyLjV2MS4zaC0zMi41Yy0xMi4xLDAtMTgtNy4yLTIzLjMtMTMuNmMtNC41LTUuNS04LjQtMTAuMi0xNS4zLTEwLjJjLTguMywwLTE0LjQsMTAuNS0yMC45LDIxLjYKCQlDNjQuNSw0NS4xLDU3LjUsNTcsNDcuNiw1N0w0Ny42LDU3eiIvPgoJPHBhdGggY2xhc3M9InN0OCIgZD0iTTQ3LjEsNTIuN2MtOSwwLTEzLjYtNC4xLTE4LjEtOGMtNC45LTQuMy05LjktOC44LTIxLjEtOC44aC01di0xLjVoNWMxMS43LDAsMTcsNC43LDIyLjEsOS4yCgkJYzQuNCwzLjksOC42LDcuNywxNyw3LjdjOC44LDAsMTUuNC05LjMsMjEuOC0xOC4zYzYuNC05LDEyLjQtMTcuNCwyMC42LTE3LjRjNywwLDExLjEsNCwxNS41LDguMmM1LjIsNSwxMSwxMC42LDIzLDEwLjZoMzUuMnYxLjUKCQlIMTI4Yy0xMi42LDAtMTguNy01LjktMjQuMS0xMS4xYy00LjMtNC4yLTgtNy44LTE0LjQtNy44Yy03LjQsMC0xMy4yLDguMi0xOS40LDE2LjhDNjMuNSw0My4xLDU2LjYsNTIuNyw0Ny4xLDUyLjdMNDcuMSw1Mi43eiIvPgoJPHBhdGggY2xhc3M9InN0OSIgZD0iTTQ2LjYsNDguNGMtOC40LDAtMTIuNy0yLjMtMTcuMi01LjNjLTQuOS0zLjMtOS45LTYtMjEuMS02YzAsMC0zLjMsMC01LjksMGMtMi41LDAtMi41LTIuOSwwLTIuOQoJCWMyLjUsMCw1LjksMCw1LjksMGMxMS43LDAsMTcuMiwzLjcsMjIuMSw2LjljNC4zLDIuOSw4LjMsNS42LDE2LjIsNS42YzguMywwLDE0LjgtNywyMS4xLTEzLjdjNi4xLTYuNSwxMS44LTEyLjcsMTkuMS0xMi43CgkJYzYuNiwwLDEwLjUsMi45LDE0LjcsNS45YzUuMiwzLjgsMTEuMSw4LDIzLjgsOGMwLDAsMzcuOCwwLDQwLjEsMGMyLjMsMCwyLjMsMi45LDAsMi45Yy0yLjMsMC00MC4xLDAtNDAuMSwwCgkJYy0xMy4yLDAtMTkuMy01LTI0LjgtOC45Yy00LjEtMy03LjctNi4xLTEzLjctNi4xYy02LjUsMC0xMiw1LjktMTcuOCwxMi4xQzYyLjQsNDEuMSw1NS42LDQ4LjQsNDYuNiw0OC40TDQ2LjYsNDguNHoiLz4KPC9nPgo8Zz4KCTxwYXRoIGQ9Ik0xNjIuNiw1Mi42YzIuNSwwLDQtMS45LDQtNXYtMC40aC0yMC40Yy0yLjQsMC0zLjYsMS4xLTMuNiwzLjZ2MjguOWgxOS44YzMuMSwwLDMuOS0zLjMsNC01bDAtMC40aC0xOC4xdi04LjVoMTEuNQoJCWMxLjIsMCwyLjUtMC45LDIuNS0yLjdjMC0xLjgtMS4yLTIuNy0yLjUtMi43aC0xMS41di03LjdIMTYyLjZ6Ii8+Cgk8cGF0aCBkPSJNMTEyLjQsNDcuMWMtMi41LDAtNCwxLjktNCw1djAuNGgxMi4zdjI3aDZ2LTI3aDguMmMyLjUsMCw0LTEuOSw0LTV2LTAuNEgxMTIuNHoiLz4KCTxwYXRoIGQ9Ik0xMDQuMiw0Ny4xYy0zLjMsMC01LjIsMS42LTUuMiw0LjJ2MTcuOGMtMy4zLTQtMTUuOS0xOS41LTE2LjYtMjAuM2MtMS4zLTEuNi0yLjgtMS42LTQuMi0xLjZoLTF2MzIuNGg1LjdWNTcuN2wxNi43LDIwLjMKCQljMS4zLDEuNiwyLjgsMS42LDQuMiwxLjZoMVY0Ny4xSDEwNC4yeiIvPgo8L2c+Cjwvc3ZnPgo="
							alt="Gå til forsiden til NTE.no"
							className={styles.headerLogo}
						/>

						<span>| KS BETA</span>
					</Link>

					<nav className={styles.headerNav}>
						<NavLink
							to="/"
							className={({ isActive }) =>
								isActive
									? styles.headerNavPageLinkActive
									: styles.headerNavPageLink
							}>
							Chat
						</NavLink>
						{' / '}
						<NavLink
							to="/qa"
							className={({ isActive }) =>
								isActive
									? styles.headerNavPageLinkActive
									: styles.headerNavPageLink
							}>
							FAQ
						</NavLink>
					</nav>

					<div className={styles.headerActions}>
						{headerActions && headerActions}
					</div>
				</div>
			</header>

			<main className={styles.main}>{children}</main>

			<button
				className={styles.piButton}
				onClick={() => navigate('/logs')}>
				&#120587;
			</button>
		</div>
	);
};

export default Layout;
