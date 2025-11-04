# queue_get() Response Structure

This document describes the structure of the response returned by `REManagerAPI.queue_get()`.

## Response Structure

The `queue_get()` method returns a dictionary with the following keys:

```python
{
    'success': bool,              # Whether the request succeeded
    'msg': str,                   # Error message (if any)
    'items': list,                # List of queue items
    'running_item': dict,         # Currently running item (if any)
    'plan_queue_uid': str         # Unique identifier for the queue state
}
```

## Items List

The `items` key contains a list of queue item dictionaries. Each item has the following structure:

```python
{
    'item_type': str,        # Type of item (e.g., 'plan')
    'name': str,             # Name of the plan/function
    'args': list,            # Positional arguments (usually empty)
    'kwargs': dict,          # Keyword arguments for the plan
    'user': str,             # User who added the item
    'user_group': str,       # User group (e.g., 'primary')
    'item_uid': str          # Unique identifier for this queue item (UUID)
}
```

## Example

```python
response = self._rem_api.queue_get()
# response:
{
    'success': True,
    'msg': '',
    'items': [
        {
            'item_type': 'plan',
            'name': 'lineup2',
            'args': [],
            'kwargs': {
                'detectors': ['noisy'],
                'mover': 'm1',
                'rel_start': -6,
                'rel_end': 6,
                'points': 61
            },
            'user': 'GUI Client',
            'user_group': 'primary',
            'item_uid': 'e36f7d3f-f728-4eea-9513-d7cebca1aa5b'
        },
        # ... more items
    ],
    'running_item': {},  # Empty if no item is running
    'plan_queue_uid': 'some-uid-string'
}
```

## Important Notes

- **`item_uid`**: This is the unique identifier used to reference queue items for operations like:
  - `item_remove_batch(uids=[...])` - Remove items by UID
  - `queue_item_move()` - Move items by UID
  - The UID remains constant throughout the item's lifetime in the queue

- **`plan_queue_uid`**: This changes whenever the queue is modified. It can be used to detect if the queue has changed since the last fetch.
