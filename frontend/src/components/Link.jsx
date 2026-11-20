/** Hash-route link: <Link to="alerts"> -> #/alerts */
export const Link = ({ to, children, ...rest }) => <a href={`#/${to}`} {...rest}>{children}</a>;
