import click
from flask.cli import with_appcontext
from app import create_app
from app.models.database import db
from app.models.user import User
import sys # <-- Add this import

# Create Flask app
app = create_app()

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    db.create_all()
    click.echo('Initialized the database.')

@click.command('create-admin')
@with_appcontext
def create_admin_command():
    """Create a default admin user."""
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@college.edu',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        click.echo('Default admin user created.')
    else:
        click.echo('Admin user already exists.')

app.cli.add_command(init_db_command)
app.cli.add_command(create_admin_command)

if __name__ == '__main__':
    # ADD THIS NEW BLOCK
    if len(sys.argv) > 1:
        if sys.argv[1] == 'init-db':
            with app.app_context():
                db.create_all()
            print('Initialized the database.')
            sys.exit()
        elif sys.argv[1] == 'create-admin':
            with app.app_context():
                if not User.query.filter_by(username='admin').first():
                    admin = User(
                        username='admin',
                        email='admin@college.edu',
                        role='admin'
                    )
                    admin.set_password('admin123')
                    db.session.add(admin)
                    db.session.commit()
                    print('Default admin user created.')
                else:
                    print('Admin user already exists.')
            sys.exit()
    # END OF NEW BLOCK
    app.run()