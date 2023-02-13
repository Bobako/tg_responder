from app.models import Chain, Message


def share_chains(session, chain_ids, account_ids):
    for chain_id in chain_ids:
        chain = session.query(Chain).filter(Chain.id == chain_id).one()
        for account_id in account_ids:
            chain_copy = Chain(
                name=chain.name,
                keywords=chain.keywords,
                turned_on=chain.turned_on,
                pause_seconds=chain.pause_seconds,
                for_group=chain.for_group,
                self_ignore=chain.self_ignore,
                in_ignore=chain.in_ignore,
                account_id=account_id,
                derived_from=chain_id
            )
            session.add(chain_copy)
            session.flush()
            session.refresh(chain_copy)
            for message in chain.messages:
                session.add(Message(
                    number=message.number,
                    type=message.type,
                    text=message.text,
                    content_path=message.content_path,
                    delay_seconds=message.delay_seconds,
                    chain_id=chain_copy.id,
                    ttl=message.ttl,
                    latitude=message.latitude,
                    longitude=message.longitude
                ))
    session.commit()


def delete_derived(session, chain_ids, account_ids):
    for chain_id in chain_ids:
        for account_id in account_ids:
            [session.delete(obj) for obj in session.query(Chain).filter(Chain.derived_from == chain_id).filter(
                Chain.account_id == account_id).all()]
    session.commit()
