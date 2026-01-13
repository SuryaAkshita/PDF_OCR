import uuid

def new_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def create_block(block_type, **kwargs):
    block = {
        "Id": new_id(block_type),
        "BlockType": block_type
    }
    block.update(kwargs)
    return block
