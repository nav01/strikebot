from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import selectinload

from session import Session
from models.server import Server
from models.user import User
from models.strike import Strike, Action
from models.strike_proponent import StrikeProponent

def __get_or_create_user(session, discord_user_id):
    user = session.query(User).filter(User.discord_user_id == discord_user_id).one_or_none()
    
    if user is None:
        user = User(discord_user_id=discord_user_id)
        session.add(user)
        
    return user
    
def __get_or_create_server(session, discord_server_id):
    server = session.query(Server).filter(Server.discord_server_id == discord_server_id).one_or_none()
    
    if server is None:
        server = Server(discord_server_id=discord_server_id)
        session.add(server)
        
    return server
        
def propose_strike(session, guild, discord_proposing_user, discord_targeted_user, reason, message_id, message_jump_url):
    proposing_user = __get_or_create_user(session, discord_proposing_user.id)
    targeted_user = __get_or_create_user(session, discord_targeted_user.id)
    server = __get_or_create_server(session, guild.id)
    strike = Strike(
        action=Action.add,
        reason=reason,
        watched_message_id=message_id,
        watched_message_jump_url=message_jump_url,
    )
    strike.proposing_user = proposing_user
    strike.targeted_user = targeted_user
    strike.server = server
    session.add(strike)
    
def add_strike_proponent(session, message_id, proponent_discord_id):
    strike = session.query(Strike).\
        options(selectinload('proponents').selectinload('user')).\
        filter(Strike.watched_message_id == message_id).one_or_none()
    
    #the message is not a strike message
    if strike is None:
        return None

    #Check if user has already reacted and been recorded. Should only happen until a handler
    #for removing reactions is added or the bot is offline during adding/removing reactions
    if any(proponent.user.discord_user_id == proponent_discord_id for proponent in strike.proponents):
        return None
        
    user = __get_or_create_user(session, proponent_discord_id)
    strike_proponent = StrikeProponent(strike_id=strike.id)
    strike_proponent.user = user
    strike.proponents.append(strike_proponent)
    return strike
    
def mark_strike_operation_successful(session, message_id, strike_level_modified):
    strike = session.query(Strike).filter(Strike.watched_message_id == message_id).one()
    strike.strike_level_modified = strike_level_modified
    strike.success = True
    strike.succeeded_at = datetime.now()
    
def create_server(session, discord_server_id):
    __get_or_create_server(session, discord_server_id)
    
def get_decayed_strikes(session, decay_time):
    highest_undecayed_strike_per_user = session.query(Strike.targeted_user_id, func.max(Strike.strike_level_modified).label('max_active_strike_level')).\
        filter(Strike.decayed == False).\
        filter(Strike.success == True).\
        filter(Strike.action == Action.add).\
        group_by(Strike.targeted_user_id).\
        subquery()
        
    #TODO change seconds to days in timedelta call
    return session.query(Strike).\
        options(selectinload('server'), selectinload('targeted_user')).\
        filter(Strike.decayed != True).\
        filter(Strike.action == Action.add).\
        filter(Strike.success == True).\
        filter(datetime.now() - timedelta(seconds=decay_time) >= Strike.succeeded_at).\
        filter(Strike.strike_level_modified == highest_undecayed_strike_per_user.c.max_active_strike_level).\
        filter(Strike.targeted_user_id == highest_undecayed_strike_per_user.c.targeted_user_id).\
        all()
    
    