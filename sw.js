self.addEventListener('push', function(event) {
    // Standard default fallback schema
    let incomingData = { title: 'Chatter', body: 'New message received!', url: '/', unread_badge: 1 };

    if (event.data) {
        try {
            incomingData = event.data.json();
        } catch (e) {
            incomingData = { title: 'Chatter', body: event.data.text(), url: '/', unread_badge: 1 };
        }
    }

    const options = {
        body: incomingData.body,
        icon: '/chatter-icon2.jpeg', // Match your manifest icon pathways
        badge: '/chatter-icon2.jpeg',
        vibrate: [100, 50, 100],
        tag: 'chatter-chat-sync',    // Grouping notifications stops them from flooding Android launchers
        renotify: true,              // Tells Android to vibrate/wake display even if tag matches
        data: {
            url: incomingData.url || '/'
        }
    };

    const promisesToWaitOn = [];

    // 1. Render notification banner
    promisesToWaitOn.push(self.registration.showNotification(incomingData.title, options));

    // 2. Resolve target Badge Context using explicit service worker scope references
    if ('setAppBadge' in self.navigator) {
        const badgeCount = parseInt(incomingData.unread_badge, 10);
        if (!isNaN(badgeCount) && badgeCount > 0) {
            promisesToWaitOn.push(self.navigator.setAppBadge(badgeCount));
        } else {
            promisesToWaitOn.push(self.navigator.clearAppBadge());
        }
    }

    event.waitUntil(Promise.all(promisesToWaitOn));
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    let targetUrl = event.notification.data?.url || '/chat.html';

    if (targetUrl.startsWith('/?') || targetUrl === '/') {
        targetUrl = targetUrl.replace('/', '/chat.html');
    }

    // --- DEEP LINK BACKUP CRUISE CONTROL ---
    // Extract the query parameters and save them straight to a permanent string
    if (targetUrl.includes('?')) {
        const queryString = targetUrl.substring(targetUrl.indexOf('?'));
        // We handle this via a postMessage loop or rely on the updated chat.html parsing below
    }
    // ----------------------------------------

    event.waitUntil(
        clients.matchAll({
            type: 'window',
            includeUncontrolled: true
        }).then((clientList) => {
            for (const client of clientList) {
                if ('focus' in client) {
                    client.focus();
                    client.navigate(targetUrl);
                    return;
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});